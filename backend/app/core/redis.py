"""Shared Redis client with graceful degradation when Redis is unavailable."""

import logging

import redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Lazy Redis wrapper that keeps the app running if Redis is down."""

    def __init__(self, url: str) -> None:
        """Try to connect; mark unavailable on failure."""
        self._url = url
        self._client: redis.Redis | None = None
        self._available = False
        self._connect()

    def _connect(self) -> None:
        """Establish a client connection when Redis responds to PING."""
        try:
            client = redis.from_url(
                self._url,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            client.ping()
        except RedisError:
            logger.warning(
                "Redis is unavailable at %s; continuing without cache",
                self._url,
            )
            self._client = None
            self._available = False
            return

        self._client = client
        self._available = True

    @property
    def available(self) -> bool:
        """Return whether Redis answered successfully on connect."""
        return self._available

    @property
    def client(self) -> redis.Redis | None:
        """Return the underlying client or None when Redis is unavailable."""
        return self._client if self._available else None


_redis_client: RedisClient | None = None


def get_redis_client() -> RedisClient:
    """Return the process-wide Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient(settings.redis_url)
    return _redis_client

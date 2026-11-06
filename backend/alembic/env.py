"""Alembic environment: reads the database URL from the application settings."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base
from app.models import *  # noqa: F401,F403  (registers models on Base.metadata)
from app.models import ANALYTICS_SCHEMA

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

MANAGED_SCHEMAS = {None, "public", ANALYTICS_SCHEMA}


def include_name(name: str | None, type_: str, parent_names: dict[str, str | None]) -> bool:
    """Limit autogenerate reflection to the schemas owned by the application.

    Args:
        name: Name of the object being reflected, or None for the default schema.
        type_: Kind of object ("schema", "table", "index", ...).
        parent_names: Names of the parent objects of the reflected one.

    Returns:
        True if autogenerate should include the object.
    """
    if type_ == "schema":
        return name in MANAGED_SCHEMAS
    return True


def run_migrations_offline() -> None:
    """Run migrations without a DB connection, emitting SQL to stdout."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_schemas=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_schemas=True,
            include_name=include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

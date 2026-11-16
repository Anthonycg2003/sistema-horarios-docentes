"""Domain exceptions raised by services and mapped to HTTP responses."""


class DomainError(Exception):
    """Base class for business-rule failures."""

    status_code: int = 500

    def __init__(self, message: str) -> None:
        """Store a human-readable error message."""
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    """Resource does not exist."""

    status_code = 404


class ConflictError(DomainError):
    """Operation conflicts with current state."""

    status_code = 409


class ValidationError(DomainError):
    """Input or state fails a business validation rule."""

    status_code = 422


class ForbiddenError(DomainError):
    """Caller is authenticated but not allowed to perform the action."""

    status_code = 403


class UnauthorizedError(DomainError):
    """Caller is not authenticated."""

    status_code = 401

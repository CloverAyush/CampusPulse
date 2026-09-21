from typing import Optional


class DomainError(Exception):
    """Base for errors that represent a rejected business action rather than a bug.
    The API layer maps these to status codes; nothing else should raise HTTP types."""

    status_code = 400
    error_code = "domain_error"

    def __init__(self, message: str, *, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code


class NotFoundError(DomainError):
    status_code = 404
    error_code = "not_found"


class PermissionDeniedError(DomainError):
    status_code = 403
    error_code = "permission_denied"


class InvalidTransitionError(DomainError):
    status_code = 409
    error_code = "invalid_transition"


class ValidationError(DomainError):
    status_code = 422
    error_code = "validation_error"


class ConflictError(DomainError):
    status_code = 409
    error_code = "conflict"


class RateLimitedError(DomainError):
    status_code = 429
    error_code = "rate_limited"

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after

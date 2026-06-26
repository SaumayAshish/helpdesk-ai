"""
Custom application exception hierarchy.

Why custom exceptions?
- Cleaner error handling than generic HTTPException everywhere
- Centralized HTTP status codes
- Easier to add logging/metrics per error type
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base class for all application exceptions."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
        )


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required"


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Insufficient permissions"


class ValidationException(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation failed"


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource conflict"


class DatabaseException(AppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Database error"

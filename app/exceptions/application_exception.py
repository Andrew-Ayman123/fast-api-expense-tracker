"""Application Exception Base Class."""
from fastapi import HTTPException, status

from app.schemas.error_schema import ErrorData


class ApplicationError(Exception):
    """Base class for all application exceptions."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> None:
        """Initialize with a message."""
        self.status_code = status_code
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        """Return the string representation of the exception."""
        return f"{self.__class__.__name__}: {self.message} (Status Code: {self.status_code})"

    def to_http_exception(self) -> HTTPException:
        """Convert the exception to an HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail=ErrorData(message=self.message).model_dump(),
        )

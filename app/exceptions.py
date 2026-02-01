"""
Custom exceptions for the AI Job Research application.

Provides structured error handling with clear error types and messages.
"""

from typing import Optional, Dict, Any


class JobResearchException(Exception):
    """Base exception for all application errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# Database Errors
class DatabaseError(JobResearchException):
    """Database operation failed"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details,
        )


class DatabaseLockError(DatabaseError):
    """Database is locked or busy"""

    def __init__(self, message: str = "Database is temporarily busy"):
        super().__init__(
            message=message,
            details={"retry_after": 5, "is_temporary": True},
        )
        self.status_code = 503


class DuplicateRecordError(DatabaseError):
    """Attempted to insert duplicate record"""

    def __init__(self, message: str, record_type: str):
        super().__init__(
            message=message,
            details={"record_type": record_type, "conflict": True},
        )
        self.status_code = 409
        self.error_code = "DUPLICATE_RECORD"


# Validation Errors
class ValidationError(JobResearchException):
    """Input validation failed"""

    def __init__(
        self, message: str, field: Optional[str] = None, value: Optional[Any] = None
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = str(value)

        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class MissingFieldError(ValidationError):
    """Required field is missing"""

    def __init__(self, field: str):
        super().__init__(
            message=f"Required field '{field}' is missing",
            field=field,
        )
        self.error_code = "MISSING_FIELD"


class InvalidFormatError(ValidationError):
    """Field has invalid format"""

    def __init__(self, field: str, expected_format: str):
        super().__init__(
            message=f"Field '{field}' has invalid format. Expected: {expected_format}",
            field=field,
        )
        self.error_code = "INVALID_FORMAT"
        self.details["expected_format"] = expected_format


# External API Errors
class ExternalAPIError(JobResearchException):
    """External API call failed"""

    def __init__(
        self,
        service: str,
        message: str,
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["service"] = service
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="EXTERNAL_API_ERROR",
            details=details,
        )


class APIAuthenticationError(ExternalAPIError):
    """API authentication failed"""

    def __init__(self, service: str):
        super().__init__(
            service=service,
            message=f"{service} authentication failed. Please check API credentials.",
            status_code=401,
        )
        self.error_code = "API_AUTH_ERROR"


class APIRateLimitError(ExternalAPIError):
    """API rate limit exceeded"""

    def __init__(self, service: str, retry_after: Optional[int] = None):
        details = {"is_temporary": True}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            service=service,
            message=f"{service} rate limit exceeded. Please try again later.",
            status_code=429,
            details=details,
        )
        self.error_code = "RATE_LIMIT_ERROR"


class APITimeoutError(ExternalAPIError):
    """API request timed out"""

    def __init__(self, service: str, timeout: float):
        super().__init__(
            service=service,
            message=f"{service} request timed out after {timeout}s",
            status_code=504,
            details={"timeout": timeout, "is_temporary": True},
        )
        self.error_code = "API_TIMEOUT"


# File Processing Errors
class FileProcessingError(JobResearchException):
    """File processing failed"""

    def __init__(self, message: str, filename: Optional[str] = None):
        details = {}
        if filename:
            details["filename"] = filename

        super().__init__(
            message=message,
            status_code=422,
            error_code="FILE_PROCESSING_ERROR",
            details=details,
        )


class InvalidFileTypeError(FileProcessingError):
    """Unsupported file type"""

    def __init__(self, filename: str, allowed_types: list):
        super().__init__(
            message=f"File type not supported. Allowed types: {', '.join(allowed_types)}",
            filename=filename,
        )
        self.error_code = "INVALID_FILE_TYPE"
        self.details["allowed_types"] = allowed_types


class FileSizeError(FileProcessingError):
    """File size exceeds limit"""

    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"File size ({size} bytes) exceeds maximum allowed ({max_size} bytes)",
        )
        self.error_code = "FILE_TOO_LARGE"
        self.details["size"] = size
        self.details["max_size"] = max_size


# Agent/LLM Errors
class AgentError(JobResearchException):
    """Agent processing failed"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="AGENT_ERROR",
            details=details,
        )


class ToolExecutionError(AgentError):
    """Agent tool execution failed"""

    def __init__(self, tool_name: str, error_message: str):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {error_message}",
            details={"tool_name": tool_name, "error": error_message},
        )
        self.error_code = "TOOL_EXECUTION_ERROR"


class LLMError(AgentError):
    """LLM API call failed"""

    def __init__(self, message: str, model: Optional[str] = None):
        details = {}
        if model:
            details["model"] = model

        super().__init__(
            message=f"LLM error: {message}",
            details=details,
        )
        self.error_code = "LLM_ERROR"


# Security Errors
class SecurityError(JobResearchException):
    """Security violation detected"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="SECURITY_ERROR",
            details=details,
        )


class InvalidAPIKeyError(SecurityError):
    """API key is invalid or missing"""

    def __init__(self, service: str):
        super().__init__(
            message=f"Invalid or missing API key for {service}",
            details={"service": service},
        )
        self.error_code = "INVALID_API_KEY"


# Resource Errors
class ResourceNotFoundError(JobResearchException):
    """Requested resource not found"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ResourceAccessError(JobResearchException):
    """User doesn't have access to resource"""

    def __init__(self, resource_type: str):
        super().__init__(
            message=f"Access denied to {resource_type}",
            status_code=403,
            error_code="ACCESS_DENIED",
            details={"resource_type": resource_type},
        )

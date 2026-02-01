"""
Tests for error handling and security features.

Tests custom exceptions, validation, API helpers, and error responses.
"""

import pytest
from fastapi.testclient import TestClient
from app.exceptions import (
    ValidationError,
    MissingFieldError,
    InvalidFormatError,
    DatabaseError,
    DatabaseLockError,
    DuplicateRecordError,
    ExternalAPIError,
    APIAuthenticationError,
    APIRateLimitError,
    InvalidFileTypeError,
    FileSizeError,
)
from app.validators import (
    validate_required_string,
    validate_optional_string,
    validate_username,
    validate_github_username,
    validate_email,
    validate_skill_list,
    validate_file_upload,
    validate_integer,
    validate_percentage,
)


class TestCustomExceptions:
    """Test custom exception classes"""

    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("Test error", field="test_field", value="bad_value")
        assert error.status_code == 400
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "test_field"
        assert "bad_value" in error.details["invalid_value"]

    def test_missing_field_error(self):
        """Test MissingFieldError"""
        error = MissingFieldError("username")
        assert error.status_code == 400
        assert "username" in error.message
        assert error.error_code == "MISSING_FIELD"

    def test_database_lock_error(self):
        """Test DatabaseLockError"""
        error = DatabaseLockError()
        assert error.status_code == 503
        assert error.details["is_temporary"] is True

    def test_duplicate_record_error(self):
        """Test DuplicateRecordError"""
        error = DuplicateRecordError("Record exists", "user")
        assert error.status_code == 409
        assert error.details["record_type"] == "user"

    def test_api_authentication_error(self):
        """Test APIAuthenticationError"""
        error = APIAuthenticationError("GitHub")
        assert error.status_code == 401
        assert "GitHub" in error.message
        assert error.details["service"] == "GitHub"

    def test_api_rate_limit_error(self):
        """Test APIRateLimitError"""
        error = APIRateLimitError("GitHub", retry_after=60)
        assert error.status_code == 429
        assert error.details["retry_after"] == 60
        assert error.details["is_temporary"] is True


class TestValidators:
    """Test input validation functions"""

    def test_validate_required_string_valid(self):
        """Test valid required string"""
        result = validate_required_string("test value", "field_name")
        assert result == "test value"

    def test_validate_required_string_missing(self):
        """Test missing required string"""
        with pytest.raises(MissingFieldError):
            validate_required_string(None, "field_name")

        with pytest.raises(MissingFieldError):
            validate_required_string("", "field_name")

    def test_validate_required_string_too_long(self):
        """Test string exceeding max length"""
        with pytest.raises(ValidationError) as exc_info:
            validate_required_string("a" * 1001, "field_name", max_length=1000)
        assert "exceeds maximum length" in str(exc_info.value)

    def test_validate_optional_string_none(self):
        """Test optional string with None"""
        result = validate_optional_string(None, "field_name")
        assert result is None

    def test_validate_optional_string_empty(self):
        """Test optional string with empty string"""
        result = validate_optional_string("", "field_name")
        assert result is None

    def test_validate_optional_string_whitespace(self):
        """Test optional string with whitespace"""
        result = validate_optional_string("  test  ", "field_name")
        assert result == "test"

    def test_validate_username_valid(self):
        """Test valid username"""
        result = validate_username("user123")
        assert result == "user123"

        result = validate_username("user-name_123")
        assert result == "user-name_123"

    def test_validate_username_invalid(self):
        """Test invalid username"""
        with pytest.raises(InvalidFormatError):
            validate_username("user@name")

        with pytest.raises(InvalidFormatError):
            validate_username("user name")

        with pytest.raises(ValidationError):
            validate_username("a" * 101)  # Too long

    def test_validate_github_username_valid(self):
        """Test valid GitHub username"""
        result = validate_github_username("octocat")
        assert result == "octocat"

        result = validate_github_username("my-username")
        assert result == "my-username"

    def test_validate_github_username_invalid(self):
        """Test invalid GitHub username"""
        with pytest.raises(InvalidFormatError):
            validate_github_username("-invalid")  # Can't start with hyphen

        with pytest.raises(InvalidFormatError):
            validate_github_username("a" * 40)  # Too long

    def test_validate_github_username_none(self):
        """Test GitHub username with None"""
        result = validate_github_username(None)
        assert result is None

    def test_validate_email_valid(self):
        """Test valid email"""
        result = validate_email("user@example.com")
        assert result == "user@example.com"

        result = validate_email("USER@EXAMPLE.COM")
        assert result == "user@example.com"  # Lowercase

    def test_validate_email_invalid(self):
        """Test invalid email"""
        with pytest.raises(InvalidFormatError):
            validate_email("not-an-email")

        with pytest.raises(InvalidFormatError):
            validate_email("@example.com")

        with pytest.raises(InvalidFormatError):
            validate_email("user@")

    def test_validate_skill_list_valid(self):
        """Test valid skill list"""
        skills = ["Python", "JavaScript", "SQL"]
        result = validate_skill_list(skills)
        assert result == skills

    def test_validate_skill_list_empty(self):
        """Test empty skill list"""
        result = validate_skill_list([])
        assert result == []

        result = validate_skill_list(None)
        assert result == []

    def test_validate_skill_list_with_whitespace(self):
        """Test skill list with whitespace"""
        skills = ["  Python  ", "JavaScript", "  ", "SQL"]
        result = validate_skill_list(skills)
        assert result == ["Python", "JavaScript", "SQL"]

    def test_validate_skill_list_invalid_type(self):
        """Test skill list with invalid type"""
        with pytest.raises(ValidationError):
            validate_skill_list("not a list")

        with pytest.raises(ValidationError):
            validate_skill_list([123, "Python"])

    def test_validate_file_upload_valid(self):
        """Test valid file upload"""
        validate_file_upload("document.pdf", 1024 * 1024)  # 1 MB
        validate_file_upload("resume.docx", 2 * 1024 * 1024)  # 2 MB

    def test_validate_file_upload_invalid_extension(self):
        """Test file with invalid extension"""
        with pytest.raises(InvalidFileTypeError):
            validate_file_upload("document.exe", 1024)

        with pytest.raises(InvalidFileTypeError):
            validate_file_upload("script.sh", 1024)

    def test_validate_file_upload_too_large(self):
        """Test file that's too large"""
        with pytest.raises(FileSizeError):
            validate_file_upload("huge.pdf", 20 * 1024 * 1024)  # 20 MB

    def test_validate_file_upload_path_traversal(self):
        """Test file with path traversal attempt"""
        with pytest.raises((ValidationError, InvalidFileTypeError)):
            validate_file_upload("../../../etc/passwd", 1024)

        with pytest.raises((ValidationError, InvalidFileTypeError)):
            validate_file_upload("dir/file.pdf", 1024)

    def test_validate_integer_valid(self):
        """Test valid integer"""
        result = validate_integer(42, "count")
        assert result == 42

    def test_validate_integer_bounds(self):
        """Test integer bounds"""
        result = validate_integer(5, "count", min_value=1, max_value=10)
        assert result == 5

        with pytest.raises(ValidationError):
            validate_integer(0, "count", min_value=1)

        with pytest.raises(ValidationError):
            validate_integer(11, "count", max_value=10)

    def test_validate_integer_optional(self):
        """Test optional integer"""
        result = validate_integer(None, "count", required=False)
        assert result is None

        with pytest.raises(MissingFieldError):
            validate_integer(None, "count", required=True)

    def test_validate_percentage_valid(self):
        """Test valid percentage"""
        result = validate_percentage(50, "progress")
        assert result == 50

        result = validate_percentage(0, "progress")
        assert result == 0

        result = validate_percentage(100, "progress")
        assert result == 100

    def test_validate_percentage_invalid(self):
        """Test invalid percentage"""
        with pytest.raises(ValidationError):
            validate_percentage(-1, "progress")

        with pytest.raises(ValidationError):
            validate_percentage(101, "progress")


class TestAPIHelpers:
    """Test API helper functions"""

    def test_call_external_api_imports(self):
        """Test that API helper functions are importable"""
        from app.api_helpers import (
            retry_async,
            call_external_api,
            call_github_api,
            call_job_search_api,
            with_error_logging,
        )
        # Just verify imports work
        assert retry_async is not None
        assert call_external_api is not None
        assert call_github_api is not None
        assert call_job_search_api is not None
        assert with_error_logging is not None


class TestSecurity:
    """Test security utilities"""

    def test_api_key_manager(self):
        """Test API key manager"""
        from app.security import APIKeyManager
        import os

        # Set a test key
        os.environ["TEST_API_KEY"] = "test_value"

        manager = APIKeyManager()
        manager._keys["TEST_API_KEY"] = "test_value"

        # Test getting configured key
        key = manager.get_key("TEST_API_KEY")
        assert key == "test_value"

        # Test checking configuration
        assert manager.is_configured("TEST_API_KEY") is True
        assert manager.is_configured("NONEXISTENT_KEY") is False

    def test_sanitize_for_logging(self):
        """Test log sanitization"""
        from app.security import sanitize_for_logging

        # Test length truncation (main feature)
        long_text = "x" * 200
        result = sanitize_for_logging(long_text, max_length=50)
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

        # Test that function works with normal strings
        normal_text = "Regular message with content"
        result = sanitize_for_logging(normal_text)
        assert result == normal_text  # Short text not modified

    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        from app.security import mask_sensitive_data

        data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "abc123",
            "normal_field": "visible",
        }

        masked = mask_sensitive_data(data)
        assert masked["username"] == "testuser"
        assert masked["password"] == "[REDACTED]"
        assert masked["api_key"] == "[REDACTED]"
        assert masked["normal_field"] == "visible"

    def test_mask_sensitive_data_nested(self):
        """Test nested data masking"""
        from app.security import mask_sensitive_data

        data = {
            "user": {
                "name": "Test",
                "token": "secret",
            },
            "config": {
                "api_key": "abc123",
            },
        }

        masked = mask_sensitive_data(data)
        assert masked["user"]["name"] == "Test"
        assert masked["user"]["token"] == "[REDACTED]"
        assert masked["config"]["api_key"] == "[REDACTED]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

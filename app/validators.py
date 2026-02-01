"""
Input validation and sanitization utilities.

Provides validation for common input types to prevent security issues
and ensure data quality.
"""

import re
from typing import Optional, List
from pathlib import Path

from app.exceptions import (
    ValidationError,
    MissingFieldError,
    InvalidFormatError,
    InvalidFileTypeError,
    FileSizeError,
)


# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_STRING_LENGTH = 10000
MAX_LIST_SIZE = 1000
MAX_USERNAME_LENGTH = 100
MAX_SKILL_LENGTH = 200

# Regex patterns
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
GITHUB_USERNAME_PATTERN = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$"
)
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

# SQL injection patterns (basic protection - parameterized queries are primary defense)
SQL_INJECTION_PATTERNS = [
    r"(\bUNION\b.*\bSELECT\b)",
    r"(\bSELECT\b.*\bFROM\b)",
    r"(\bINSERT\b.*\bINTO\b)",
    r"(\bDELETE\b.*\bFROM\b)",
    r"(\bDROP\b.*\bTABLE\b)",
    r"(\bUPDATE\b.*\bSET\b)",
    r"(--)",
    r"(;.*\b(DROP|DELETE|UPDATE|INSERT)\b)",
]


def validate_required_string(
    value: Optional[str],
    field_name: str,
    max_length: int = MAX_STRING_LENGTH,
    min_length: int = 1,
) -> str:
    """Validate a required string field"""
    if value is None or value == "":
        raise MissingFieldError(field_name)

    if not isinstance(value, str):
        raise ValidationError(
            f"Field '{field_name}' must be a string", field=field_name, value=value
        )

    value = value.strip()

    if len(value) < min_length:
        raise ValidationError(
            f"Field '{field_name}' must be at least {min_length} characters",
            field=field_name,
        )

    if len(value) > max_length:
        raise ValidationError(
            f"Field '{field_name}' exceeds maximum length of {max_length} characters",
            field=field_name,
        )

    return value


def validate_optional_string(
    value: Optional[str],
    field_name: str,
    max_length: int = MAX_STRING_LENGTH,
) -> Optional[str]:
    """Validate an optional string field"""
    if value is None or value == "":
        return None

    if not isinstance(value, str):
        raise ValidationError(
            f"Field '{field_name}' must be a string", field=field_name, value=value
        )

    value = value.strip()

    if len(value) > max_length:
        raise ValidationError(
            f"Field '{field_name}' exceeds maximum length of {max_length} characters",
            field=field_name,
        )

    return value if value else None


def validate_username(username: str) -> str:
    """Validate username format"""
    username = validate_required_string(
        username, "username", max_length=MAX_USERNAME_LENGTH
    )

    if not USERNAME_PATTERN.match(username):
        raise InvalidFormatError(
            "username",
            "alphanumeric characters, hyphens, and underscores only (1-100 chars)",
        )

    return username


def validate_github_username(username: Optional[str]) -> Optional[str]:
    """Validate GitHub username format"""
    if not username:
        return None

    username = username.strip()

    if not GITHUB_USERNAME_PATTERN.match(username):
        raise InvalidFormatError(
            "github_username",
            "valid GitHub username (1-39 chars, alphanumeric and hyphens)",
        )

    return username


def validate_email(email: str) -> str:
    """Validate email format"""
    email = validate_required_string(email, "email", max_length=254)

    if not EMAIL_PATTERN.match(email):
        raise InvalidFormatError("email", "valid email address")

    return email.lower()


def validate_url(url: Optional[str], field_name: str = "url") -> Optional[str]:
    """Validate URL format"""
    if not url:
        return None

    url = url.strip()

    if not URL_PATTERN.match(url):
        raise InvalidFormatError(field_name, "valid URL (http:// or https://)")

    return url


def validate_skill_list(skills: Optional[List[str]]) -> List[str]:
    """Validate list of skills"""
    if skills is None:
        return []

    if not isinstance(skills, list):
        raise ValidationError("Skills must be a list", field="skills")

    if len(skills) > MAX_LIST_SIZE:
        raise ValidationError(
            f"Skills list exceeds maximum size of {MAX_LIST_SIZE}",
            field="skills",
        )

    validated_skills = []
    for i, skill in enumerate(skills):
        if not isinstance(skill, str):
            raise ValidationError(
                f"Skill at index {i} must be a string",
                field=f"skills[{i}]",
                value=skill,
            )

        skill = skill.strip()
        if not skill:
            continue  # Skip empty strings

        if len(skill) > MAX_SKILL_LENGTH:
            raise ValidationError(
                f"Skill '{skill[:50]}...' exceeds maximum length of {MAX_SKILL_LENGTH}",
                field=f"skills[{i}]",
            )

        validated_skills.append(skill)

    return validated_skills


def validate_file_upload(
    filename: str,
    file_size: int,
    allowed_extensions: Optional[set] = None,
    max_size: int = MAX_FILE_SIZE,
) -> None:
    """Validate file upload parameters"""
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_FILE_EXTENSIONS

    # Validate file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise InvalidFileTypeError(filename, list(allowed_extensions))

    # Validate file size
    if file_size > max_size:
        raise FileSizeError(file_size, max_size)

    # Basic filename sanitization check
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValidationError(
            "Invalid filename: path traversal attempt detected",
            field="filename",
            value=filename,
        )


def sanitize_sql_input(value: str) -> str:
    """
    Basic SQL injection pattern detection.

    Note: This is NOT a replacement for parameterized queries,
    which should always be used. This is defense in depth.
    """
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                "Input contains potentially dangerous SQL patterns",
                field="input",
            )

    return value


def validate_integer(
    value: Optional[int],
    field_name: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    required: bool = True,
) -> Optional[int]:
    """Validate integer value with optional bounds"""
    if value is None:
        if required:
            raise MissingFieldError(field_name)
        return None

    if not isinstance(value, int):
        raise ValidationError(
            f"Field '{field_name}' must be an integer",
            field=field_name,
            value=value,
        )

    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Field '{field_name}' must be at least {min_value}",
            field=field_name,
            value=value,
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Field '{field_name}' must not exceed {max_value}",
            field=field_name,
            value=value,
        )

    return value


def validate_float(
    value: Optional[float],
    field_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    required: bool = True,
) -> Optional[float]:
    """Validate float value with optional bounds"""
    if value is None:
        if required:
            raise MissingFieldError(field_name)
        return None

    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"Field '{field_name}' must be a number",
            field=field_name,
            value=value,
        )

    value = float(value)

    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Field '{field_name}' must be at least {min_value}",
            field=field_name,
            value=value,
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Field '{field_name}' must not exceed {max_value}",
            field=field_name,
            value=value,
        )

    return value


def validate_percentage(value: Optional[int], field_name: str) -> Optional[int]:
    """Validate percentage value (0-100)"""
    return validate_integer(
        value,
        field_name,
        min_value=0,
        max_value=100,
        required=False,
    )

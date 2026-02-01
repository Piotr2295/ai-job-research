"""
Security utilities for the application.

Provides API key management, rate limiting helpers, and security checks.
"""

import os
import logging
from typing import Optional, Dict

from app.exceptions import InvalidAPIKeyError

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API keys with validation and caching"""

    def __init__(self):
        self._keys: Dict[str, Optional[str]] = {}
        self._load_keys()

    def _load_keys(self):
        """Load all API keys from environment"""
        key_names = [
            "OPENAI_API_KEY",
            "GITHUB_TOKEN",
            "RAPIDAPI_KEY",
            "PINECONE_API_KEY",
        ]

        for key_name in key_names:
            value = os.getenv(key_name)
            self._keys[key_name] = value

            if value:
                # Log that key is present (but not the actual key!)
                logger.info(f"{key_name} loaded successfully")
            else:
                logger.warning(f"{key_name} not found in environment")

    def get_key(self, key_name: str, required: bool = False) -> Optional[str]:
        """
        Get an API key.

        Args:
            key_name: Name of the environment variable
            required: If True, raise error if key is missing

        Returns:
            API key value or None if not found

        Raises:
            InvalidAPIKeyError: If required=True and key is missing
        """
        key = self._keys.get(key_name)

        if required and not key:
            service_name = key_name.replace("_API_KEY", "").replace("_TOKEN", "")
            raise InvalidAPIKeyError(service_name)

        return key

    def is_configured(self, key_name: str) -> bool:
        """Check if an API key is configured"""
        return bool(self._keys.get(key_name))


# Global instance
api_key_manager = APIKeyManager()


def get_api_key(key_name: str, required: bool = False) -> Optional[str]:
    """
    Get an API key from the manager.

    Args:
        key_name: Name of the environment variable
        required: If True, raise error if key is missing

    Returns:
        API key value or None
    """
    return api_key_manager.get_key(key_name, required=required)


def is_api_configured(key_name: str) -> bool:
    """Check if an API service is configured"""
    return api_key_manager.is_configured(key_name)


def sanitize_for_logging(text: str, max_length: int = 100) -> str:
    """
    Sanitize text for safe logging.

    Removes potential sensitive data and truncates long strings.
    """
    if not text:
        return ""

    # Remove potential API keys (hex or alphanumeric with underscores/hyphens, 20+ chars)
    import re

    text = re.sub(
        r"(?:api[_-]?key|token|password|secret|authorization)[:\s=]+[A-Za-z0-9_\-]{20,}",
        "[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def validate_rate_limit_key(key: str) -> str:
    """
    Validate and sanitize rate limit key (typically IP address).

    Ensures the key doesn't contain path traversal or injection attempts.
    """
    # Basic validation
    if not key or len(key) > 100:
        return "unknown"

    # Remove any suspicious characters
    import re

    # Allow only alphanumeric, dots, colons, hyphens (for IPs and IPv6)
    sanitized = re.sub(r"[^a-zA-Z0-9.:_-]", "", key)

    return sanitized or "unknown"


def get_client_identifier(request) -> str:
    """
    Get a safe client identifier for rate limiting.

    Uses X-Forwarded-For if behind proxy, falls back to client IP.
    """
    # Check if behind a proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return validate_rate_limit_key(client_ip)


class SecurityHeaders:
    """Security headers to add to responses"""

    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
        }


def mask_sensitive_data(data: dict, keys_to_mask: set = None) -> dict:
    """
    Mask sensitive data in a dictionary for logging.

    Args:
        data: Dictionary containing potentially sensitive data
        keys_to_mask: Set of keys to mask (default includes common sensitive keys)

    Returns:
        Dictionary with sensitive values masked
    """
    if keys_to_mask is None:
        keys_to_mask = {
            "password",
            "token",
            "api_key",
            "secret",
            "authorization",
            "auth",
            "apikey",
            "api-key",
        }

    masked_data = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in keys_to_mask):
            masked_data[key] = "[REDACTED]"
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value, keys_to_mask)
        elif isinstance(value, list):
            masked_data[key] = [
                (
                    mask_sensitive_data(item, keys_to_mask)
                    if isinstance(item, dict)
                    else item
                )
                for item in value
            ]
        else:
            masked_data[key] = value

    return masked_data

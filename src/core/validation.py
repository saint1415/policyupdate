"""
Input Validation Module
Security-focused input validation and sanitization
"""

import re
from typing import Optional, List


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.

    Args:
        filename: Raw filename input

    Returns:
        Sanitized filename safe for filesystem operations

    Raises:
        ValidationError: If filename is invalid
    """
    if not filename:
        raise ValidationError("Filename cannot be empty")

    # Check for path traversal patterns (../ or ..\)
    if re.search(r'\.\.[\\/]', filename) or filename.startswith('..'):
        raise ValidationError("Invalid filename: path traversal detected")

    # Remove path components - keep only the final filename
    filename = filename.replace('\\', '/').split('/')[-1]

    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)

    # Check that result doesn't start with ..
    if filename.startswith('..'):
        raise ValidationError("Invalid filename: path traversal detected")

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    if not filename:
        raise ValidationError("Filename contains only invalid characters")

    return filename


def sanitize_client_name(name: str) -> str:
    """
    Sanitize client name input.

    Args:
        name: Raw client name

    Returns:
        Sanitized client name

    Raises:
        ValidationError: If name is invalid
    """
    if not name:
        raise ValidationError("Client name cannot be empty")

    # Strip whitespace
    name = name.strip()

    # Remove control characters
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)

    # Limit length
    if len(name) > 200:
        name = name[:200]

    if len(name) < 2:
        raise ValidationError("Client name must be at least 2 characters")

    return name


def validate_framework_id(framework_id: str, valid_ids: List[str]) -> str:
    """
    Validate a framework ID against known frameworks.

    Args:
        framework_id: The framework ID to validate
        valid_ids: List of valid framework IDs

    Returns:
        Validated framework ID

    Raises:
        ValidationError: If framework ID is invalid
    """
    if not framework_id:
        raise ValidationError("Framework ID cannot be empty")

    framework_id = framework_id.strip().lower()

    # Only allow alphanumeric, underscore, hyphen, and dot
    if not re.match(r'^[a-z0-9_.-]+$', framework_id):
        raise ValidationError("Invalid framework ID format")

    if framework_id not in valid_ids:
        raise ValidationError(f"Unknown framework: {framework_id}")

    return framework_id


def validate_policy_id(policy_id: str) -> str:
    """
    Validate a policy ID format.

    Args:
        policy_id: The policy ID to validate

    Returns:
        Validated policy ID

    Raises:
        ValidationError: If policy ID is invalid
    """
    if not policy_id:
        raise ValidationError("Policy ID cannot be empty")

    policy_id = policy_id.strip().lower()

    # Only allow alphanumeric, hyphen, and underscore
    if not re.match(r'^[a-z0-9_-]+$', policy_id):
        raise ValidationError("Invalid policy ID format")

    if len(policy_id) > 200:
        raise ValidationError("Policy ID too long")

    return policy_id


def validate_email(email: str) -> str:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Validated email

    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty")

    email = email.strip().lower()

    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")

    if len(email) > 254:
        raise ValidationError("Email address too long")

    return email


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """
    Validate URL format.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes (default: https, http)

    Returns:
        Validated URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")

    if allowed_schemes is None:
        allowed_schemes = ['https', 'http']

    url = url.strip()

    # Check scheme
    scheme_match = re.match(r'^([a-z]+)://', url.lower())
    if not scheme_match:
        raise ValidationError("URL must include scheme (http/https)")

    scheme = scheme_match.group(1)
    if scheme not in allowed_schemes:
        raise ValidationError(f"URL scheme must be one of: {', '.join(allowed_schemes)}")

    # Basic URL pattern
    pattern = r'^https?://[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+.*$'
    if not re.match(pattern, url):
        raise ValidationError("Invalid URL format")

    if len(url) > 2000:
        raise ValidationError("URL too long")

    return url


def sanitize_search_query(query: str, max_length: int = 200) -> str:
    """
    Sanitize a search query string.

    Args:
        query: Raw search query
        max_length: Maximum allowed length

    Returns:
        Sanitized search query
    """
    if not query:
        return ""

    # Strip whitespace
    query = query.strip()

    # Remove control characters
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)

    # Limit length
    if len(query) > max_length:
        query = query[:max_length]

    return query


def validate_integer(value: str, min_val: Optional[int] = None,
                    max_val: Optional[int] = None, name: str = "value") -> int:
    """
    Validate and convert string to integer.

    Args:
        value: String value to convert
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the parameter (for error messages)

    Returns:
        Validated integer

    Raises:
        ValidationError: If value is invalid
    """
    try:
        result = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be an integer")

    if min_val is not None and result < min_val:
        raise ValidationError(f"{name} must be at least {min_val}")

    if max_val is not None and result > max_val:
        raise ValidationError(f"{name} must be at most {max_val}")

    return result

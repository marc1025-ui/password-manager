"""
Password generation and strength validation module.
Provides secure password generation with customizable parameters
and comprehensive password strength validation.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass


@dataclass
class StrengthResult:
    """
    Result of password strength validation.

    Attributes:
        ok: True if password meets all requirements
        reasons: List of reasons why password failed validation
    """

    ok: bool
    reasons: list[str]


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_specials: bool = True,
) -> str:
    """
    Generate a cryptographically secure random password.

    Args:
        length: Password length (default: 16)
        use_upper: Include uppercase letters A-Z
        use_lower: Include lowercase letters a-z
        use_digits: Include digits 0-9
        use_specials: Include special characters !@#$%^&*()_+-=[]{}|;:,.<>?

    Returns:
        Randomly generated password string

    Raises:
        ValueError: If no character types are selected

    Examples:
        >>> generate_password(12, use_specials=False)
        'Kj8mN2pQ9rL4'
        >>> generate_password(8, use_upper=False, use_lower=True, use_digits=True)
        'k8j2m9p4'
    """
    # Character sets
    charset = ""
    if use_upper:
        charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if use_lower:
        charset += "abcdefghijklmnopqrstuvwxyz"
    if use_digits:
        charset += "0123456789"
    if use_specials:
        charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Validate that at least one character type is selected
    if not charset:
        raise ValueError("At least one character type must be selected")

    # Generate password using cryptographically secure random
    return "".join(secrets.choice(charset) for _ in range(length))


def validate_password_strength(
    password: str, min_length: int = 8, require_types: int = 3
) -> StrengthResult:
    """
    Validate password strength against security criteria.

    Args:
        password: Password to validate
        min_length: Minimum required length
        require_types: Number of character types required (1-4)
                      1: Any characters
                      2: Mix of 2 types (e.g., letters + digits)
                      3: Mix of 3 types (e.g., upper + lower + digits)
                      4: All types (upper + lower + digits + special)

    Returns:
        StrengthResult with validation result and failure reasons

    Examples:
        >>> result = validate_password_strength("Password123!")
        >>> result.ok
        True
        >>> result = validate_password_strength("weak")
        >>> result.ok
        False
        >>> "too short" in " ".join(result.reasons)
        True
    """
    reasons = []

    # Check minimum length
    if len(password) < min_length:
        reasons.append(f"Password must be at least {min_length} characters long")

    # Check for empty password
    if not password:
        reasons.append("Password cannot be empty")
        return StrengthResult(ok=False, reasons=reasons)

    # Character type detection
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"[0-9]", password))
    has_special = bool(re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password))

    # Count present character types
    types_present = sum([has_upper, has_lower, has_digit, has_special])

    # Check character type requirements
    if types_present < require_types:
        reasons.append(
            f"Password must contain at least {require_types} character types "
            "(uppercase, lowercase, digits, special characters)."
        )

    # Check for common weak patterns
    if password.lower() in [
        "password",
        "123456",
        "qwerty",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
    ]:
        reasons.append("Password is too common and easily guessable")

    # Check for simple patterns
    if re.match(r"^(.)\1+$", password):  # All same character
        reasons.append("Password cannot be all the same character")

    if re.match(r"^(012|123|234|345|456|567|678|789|890)+", password):
        reasons.append("Password contains predictable number sequences")

    if re.match(r"^(abc|def|ghi|jkl|mno|pqr|stu|vwx)+", password.lower()):
        reasons.append("Password contains predictable letter sequences")

    # Additional strength checks for very short passwords
    if len(password) < 6:
        reasons.append("Password is critically short (less than 6 characters)")

    # Check for keyboard patterns (basic)
    keyboard_patterns = ["qwerty", "asdf", "zxcv", "1234", "abcd"]
    password_lower = password.lower()
    for pattern in keyboard_patterns:
        if pattern in password_lower:
            reasons.append("Password contains keyboard patterns")
            break

    return StrengthResult(ok=len(reasons) == 0, reasons=reasons)

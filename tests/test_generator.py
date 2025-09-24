"""
Comprehensive tests for password generation and validation.
Tests secure password generation with various parameters and
strength validation against security criteria.
"""

import unittest

from core.generator import StrengthResult, generate_password, validate_password_strength


class TestPasswordGeneration(unittest.TestCase):
    """Tests for secure password generation functionality."""

    def test_generate_password_default(self):
        """Test password generation with default parameters."""
        password = generate_password()

        assert isinstance(password, str)
        assert len(password) == 16  # Default length

    def test_generate_password_custom_length(self):
        """Test password generation with custom lengths."""
        for length in [8, 12, 20, 32, 64]:
            with self.subTest(length=length):
                password = generate_password(length=length)
                assert len(password) == length

    def test_generate_password_only_lowercase(self):
        """Test generation with only lowercase letters."""
        password = generate_password(
            length=20,
            use_upper=False,
            use_lower=True,
            use_digits=False,
            use_specials=False,
        )

        assert all(c.islower() for c in password)
        assert not any(c.isupper() for c in password)
        assert not any(c.isdigit() for c in password)

    def test_generate_password_only_uppercase(self):
        """Test generation with only uppercase letters."""
        password = generate_password(
            length=20,
            use_upper=True,
            use_lower=False,
            use_digits=False,
            use_specials=False,
        )

        assert all(c.isupper() for c in password)
        assert not any(c.islower() for c in password)
        assert not any(c.isdigit() for c in password)

    def test_generate_password_only_digits(self):
        """Test generation with only digits."""
        password = generate_password(
            length=20,
            use_upper=False,
            use_lower=False,
            use_digits=True,
            use_specials=False,
        )

        assert all(c.isdigit() for c in password)
        assert not any(c.isalpha() for c in password)

    def test_generate_password_only_specials(self):
        """Test generation with only special characters."""
        password = generate_password(
            length=20,
            use_upper=False,
            use_lower=False,
            use_digits=False,
            use_specials=True,
        )

        # All characters should be special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert all(c in special_chars for c in password)
        assert not any(c.isalnum() for c in password)

    def test_generate_password_mixed_characters(self):
        """Test generation with mix of all character types."""
        password = generate_password(
            length=50,  # Sufficient length to have all types
            use_upper=True,
            use_lower=True,
            use_digits=True,
            use_specials=True,
        )

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        # With length 50, we should have all types
        assert has_upper, "Should contain uppercase letters"
        assert has_lower, "Should contain lowercase letters"
        assert has_digit, "Should contain digits"
        assert has_special, "Should contain special characters"

    def test_generate_password_randomness(self):
        """Test that generated passwords are different (randomness)."""
        passwords = [generate_password(length=20) for _ in range(10)]

        # All passwords should be unique
        unique_passwords = set(passwords)
        assert len(unique_passwords) == len(passwords)

    def test_generate_password_no_character_types(self):
        """Test with no character types selected should raise error."""
        with self.assertRaises(ValueError):
            generate_password(
                use_upper=False,
                use_lower=False,
                use_digits=False,
                use_specials=False,
            )

    def test_generate_password_minimum_length(self):
        """Test with minimum length."""
        password = generate_password(length=1)
        assert len(password) == 1

    def test_generate_password_very_long(self):
        """Test with very long password."""
        password = generate_password(length=1000)
        assert len(password) == 1000


class TestPasswordStrengthValidation(unittest.TestCase):
    """Tests for password strength validation functionality."""

    def test_strong_password(self):
        """Test validation of a strong password."""
        strong_password = "MyStr0ng!P@ssw0rd2024"  # nosec: test password
        result = validate_password_strength(strong_password)

        assert isinstance(result, StrengthResult)
        assert result.ok
        assert len(result.reasons) == 0

    def test_too_short_password(self):
        """Test validation of password that's too short."""
        short_password = "Abc1!"  # nosec: test password
        result = validate_password_strength(short_password, min_length=12)

        assert not result.ok
        assert "at least 12 characters" in " ".join(result.reasons)

    def test_password_without_uppercase(self):
        """Test password missing uppercase letters."""
        no_upper_password = "mypassword123!"  # nosec: test password
        result = validate_password_strength(no_upper_password, require_types=4)

        assert not result.ok
        assert any("character types" in reason.lower() for reason in result.reasons)

    def test_password_without_lowercase(self):
        """Test password missing lowercase letters."""
        no_lower_password = "MYPASSWORD123!"  # nosec: test password
        result = validate_password_strength(no_lower_password, require_types=4)

        assert not result.ok
        assert any("character types" in reason.lower() for reason in result.reasons)

    def test_password_without_digits(self):
        """Test password missing digits."""
        no_digits_password = "MyPassword!"  # nosec: test password
        result = validate_password_strength(no_digits_password, require_types=4)

        assert not result.ok
        assert any("character types" in reason.lower() for reason in result.reasons)

    def test_password_without_special_chars(self):
        """Test password missing special characters."""
        no_special_password = "MyPassword123"  # nosec: test password
        result = validate_password_strength(no_special_password, require_types=4)

        assert not result.ok
        assert any("character types" in reason.lower() for reason in result.reasons)

    def test_common_password(self):
        """Test validation of common weak passwords."""
        common_passwords = ["password", "123456", "qwerty", "admin"]  # nosec: test passwords

        for password in common_passwords:
            with self.subTest(password=password):
                result = validate_password_strength(password)
                # Common passwords should be rejected
                assert not result.ok

    def test_empty_password(self):
        """Test validation of empty password."""
        result = validate_password_strength("")

        assert not result.ok
        assert "cannot be empty" in " ".join(result.reasons)


class TestPasswordGeneratorIntegration(unittest.TestCase):
    """Integration tests between password generation and validation."""

    def test_generated_passwords_meet_requirements(self):
        """Test that generated passwords pass strength validation."""
        for length in [12, 16, 20, 32]:
            with self.subTest(length=length):
                password = generate_password(
                    length=length,
                    use_upper=True,
                    use_lower=True,
                    use_digits=True,
                    use_specials=True,
                )

                result = validate_password_strength(
                    password, min_length=length, require_types=4
                )

                self.assertTrue(
                    result.ok,
                    f"Generated password '{password}' doesn't meet requirements: {result.reasons}",
                )

    def test_generated_passwords_are_strong(self):
        """Test that generated passwords are considered strong."""
        for _ in range(10):  # Test multiple generations
            password = generate_password(
                length=16,
                use_upper=True,
                use_lower=True,
                use_digits=True,
                use_specials=True,
            )

            result = validate_password_strength(password)
            self.assertTrue(
                result.ok,
                f"Generated password '{password}' not considered strong: {result.reasons}",
            )

    def test_weak_generated_passwords(self):
        """Test intentional generation of weak passwords."""
        weak_password = generate_password(
            length=4,  # Very short
            use_upper=False,
            use_lower=True,
            use_digits=False,
            use_specials=False,
        )

        result = validate_password_strength(
            weak_password, min_length=12, require_types=4
        )
        assert not result.ok, "Weak password should not pass strict validation"


if __name__ == "__main__":
    unittest.main()

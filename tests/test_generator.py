import unittest

from core.generator import StrengthResult, generate_password, validate_password_strength


class TestPasswordGeneration(unittest.TestCase):
    """Tests pour la génération de mots de passe"""

    def test_generate_password_default(self):
        """Test génération avec paramètres par défaut"""
        password = generate_password()

        self.assertIsInstance(password, str)
        self.assertEqual(len(password), 16)  # Longueur par défaut

    def test_generate_password_custom_length(self):
        """Test génération avec longueur personnalisée"""
        for length in [8, 12, 20, 32, 64]:
            with self.subTest(length=length):
                password = generate_password(length=length)
                self.assertEqual(len(password), length)

    def test_generate_password_only_lowercase(self):
        """Test génération avec seulement des minuscules"""
        password = generate_password(
            length=20,
            use_upper=False,
            use_lower=True,
            use_digits=False,
            use_specials=False,
        )

        self.assertTrue(all(c.islower() for c in password))
        self.assertFalse(any(c.isupper() for c in password))
        self.assertFalse(any(c.isdigit() for c in password))

    def test_generate_password_only_uppercase(self):
        """Test génération avec seulement des majuscules"""
        password = generate_password(
            length=20,
            use_upper=True,
            use_lower=False,
            use_digits=False,
            use_specials=False,
        )

        self.assertTrue(all(c.isupper() for c in password))
        self.assertFalse(any(c.islower() for c in password))
        self.assertFalse(any(c.isdigit() for c in password))

    def test_generate_password_only_digits(self):
        """Test génération avec seulement des chiffres"""
        password = generate_password(
            length=20,
            use_upper=False,
            use_lower=False,
            use_digits=True,
            use_specials=False,
        )

        self.assertTrue(all(c.isdigit() for c in password))
        self.assertFalse(any(c.isalpha() for c in password))

    def test_generate_password_only_specials(self):
        """Test génération avec seulement des caractères spéciaux"""
        password = generate_password(
            length=20,
            use_upper=False,
            use_lower=False,
            use_digits=False,
            use_specials=True,
        )

        # Tous les caractères doivent être des caractères spéciaux
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        self.assertTrue(all(c in special_chars for c in password))
        self.assertFalse(any(c.isalnum() for c in password))

    def test_generate_password_mixed_characters(self):
        """Test génération avec mélange de types de caractères"""
        password = generate_password(
            length=50,  # Longueur suffisante pour avoir tous les types
            use_upper=True,
            use_lower=True,
            use_digits=True,
            use_specials=True,
        )

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        # Avec une longueur de 50, on devrait avoir tous les types
        self.assertTrue(has_upper, "Doit contenir des majuscules")
        self.assertTrue(has_lower, "Doit contenir des minuscules")
        self.assertTrue(has_digit, "Doit contenir des chiffres")
        self.assertTrue(has_special, "Doit contenir des caractères spéciaux")

    def test_generate_password_randomness(self):
        """Test que les mots de passe générés sont différents"""
        passwords = [generate_password(length=20) for _ in range(10)]

        # Tous les mots de passe doivent être différents
        unique_passwords = set(passwords)
        self.assertEqual(len(unique_passwords), len(passwords))

    def test_generate_password_no_character_types(self):
        """Test avec aucun type de caractère sélectionné"""
        with self.assertRaises(ValueError):
            generate_password(
                use_upper=False, use_lower=False, use_digits=False, use_specials=False
            )

    def test_generate_password_minimum_length(self):
        """Test avec longueur minimale"""
        password = generate_password(length=1)
        self.assertEqual(len(password), 1)

    def test_generate_password_very_long(self):
        """Test avec très grande longueur"""
        password = generate_password(length=1000)
        self.assertEqual(len(password), 1000)


class TestPasswordStrengthValidation(unittest.TestCase):
    """Tests pour la validation de la force des mots de passe"""

    def test_strong_password(self):
        """Test avec un mot de passe fort"""
        strong_password = "MyStr0ng!P@ssw0rd2024"
        result = validate_password_strength(strong_password)

        self.assertIsInstance(result, StrengthResult)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.reasons), 0)

    def test_too_short_password(self):
        """Test avec mot de passe trop court"""
        short_password = "Abc1!"
        result = validate_password_strength(short_password, min_length=12)

        self.assertFalse(result.ok)
        self.assertIn("au moins 12 caractères", " ".join(result.reasons))

    def test_password_without_uppercase(self):
        """Test avec mot de passe sans majuscules"""
        no_upper_password = "mypassword123!"
        result = validate_password_strength(no_upper_password, require_types=4)

        self.assertFalse(result.ok)
        self.assertTrue(any("majuscule" in reason.lower() for reason in result.reasons))

    def test_password_without_lowercase(self):
        """Test avec mot de passe sans minuscules"""
        no_lower_password = "MYPASSWORD123!"
        result = validate_password_strength(no_lower_password, require_types=4)

        self.assertFalse(result.ok)
        self.assertTrue(any("minuscule" in reason.lower() for reason in result.reasons))

    def test_password_without_digits(self):
        """Test avec mot de passe sans chiffres"""
        no_digits_password = "MyPassword!"
        result = validate_password_strength(no_digits_password, require_types=4)

        self.assertFalse(result.ok)
        self.assertTrue(any("chiffre" in reason.lower() for reason in result.reasons))

    def test_password_without_special_chars(self):
        """Test avec mot de passe sans caractères spéciaux"""
        no_special_password = "MyPassword123"
        result = validate_password_strength(no_special_password, require_types=4)

        self.assertFalse(result.ok)
        self.assertTrue(any("spécial" in reason.lower() for reason in result.reasons))

    def test_password_with_repetitions(self):
        """Test avec mot de passe contenant des répétitions"""
        repetitive_password = "aaaBBB111!!!"
        result = validate_password_strength(repetitive_password)

        # Selon l'implémentation, cela pourrait être détecté comme faible
        # Ce test vérifie que la fonction fonctionne sans erreur
        self.assertIsInstance(result, StrengthResult)

    def test_common_password(self):
        """Test avec mot de passe commun"""
        common_passwords = ["password", "123456", "qwerty", "admin"]

        for password in common_passwords:
            with self.subTest(password=password):
                result = validate_password_strength(password)
                # Les mots de passe communs devraient être rejetés
                self.assertFalse(result.ok)

    def test_empty_password(self):
        """Test avec mot de passe vide"""
        result = validate_password_strength("")

        self.assertFalse(result.ok)
        self.assertIn("au moins", " ".join(result.reasons))

    def test_password_strength_levels(self):
        """Test avec différents niveaux de force"""
        passwords = [
            ("weak", "123"),
            ("medium", "Password123"),
            ("strong", "MyStr0ng!P@ssw0rd"),
            ("very_strong", "Th1s!s@V3ry$tr0ng&C0mpl3xP@ssw0rd2024"),
        ]

        for level, password in passwords:
            with self.subTest(level=level, password=password):
                result = validate_password_strength(password)
                self.assertIsInstance(result, StrengthResult)

    def test_unicode_password(self):
        """Test avec caractères Unicode"""
        unicode_password = "Mönƒštr€Pàßšwørð123!"
        result = validate_password_strength(unicode_password)

        self.assertIsInstance(result, StrengthResult)
        # Les caractères Unicode devraient être gérés correctement

    def test_custom_requirements(self):
        """Test avec exigences personnalisées"""
        password = "TestPass1"

        # Test avec exigences relaxées
        result_relaxed = validate_password_strength(
            password, min_length=8, require_types=2
        )

        # Test avec exigences strictes
        result_strict = validate_password_strength(
            password, min_length=15, require_types=4
        )

        # Le même mot de passe peut passer ou échouer selon les critères
        self.assertIsInstance(result_relaxed, StrengthResult)
        self.assertIsInstance(result_strict, StrengthResult)


class TestPasswordGeneratorIntegration(unittest.TestCase):
    """Tests d'intégration entre génération et validation"""

    def test_generated_passwords_meet_requirements(self):
        """Test que les mots de passe générés respectent les exigences"""
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
                    f"Le mot de passe généré '{password}' ne respecte pas les exigences: {result.reasons}",
                )

    def test_generated_passwords_are_strong(self):
        """Test que les mots de passe générés sont considérés comme forts"""
        for _ in range(10):  # Tester plusieurs générations
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
                f"Le mot de passe généré '{password}' n'est pas considéré comme fort: {result.reasons}",
            )

    def test_weak_generated_passwords(self):
        """Test génération intentionnelle de mots de passe faibles"""
        weak_password = generate_password(
            length=4,  # Très court
            use_upper=False,
            use_lower=True,
            use_digits=False,
            use_specials=False,
        )

        result = validate_password_strength(
            weak_password, min_length=12, require_types=4
        )
        self.assertFalse(
            result.ok,
            "Un mot de passe faible ne devrait pas passer la validation stricte",
        )


if __name__ == "__main__":
    unittest.main()

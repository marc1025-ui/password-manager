"""
Comprehensive tests for cryptographic modules.
Tests key derivation, keyring management, and AEAD encryption
to ensure security and reliability of the password manager.
"""

import os
import unittest

from crypto import aead
from crypto.key_derivation import KDFParams, derive_key
from crypto.keyring import Keyring


class TestKDFParams(unittest.TestCase):
    """Tests pour la classe KDFParams"""

    def test_kdf_params_creation(self):
        """Test de création d'un objet KDFParams"""
        salt = os.urandom(16)
        params = KDFParams(
            time_cost=2,
            memory_cost=256*1024,
            parallelism=4,
            salt=salt,
            hash_len=32
        )

        self.assertEqual(params.time_cost, 2)
        self.assertEqual(params.memory_cost, 256*1024)
        self.assertEqual(params.parallelism, 4)
        self.assertEqual(params.salt, salt)
        self.assertEqual(params.hash_len, 32)

    def test_kdf_params_to_dict(self):
        """Test de conversion KDFParams vers dictionnaire"""
        salt = os.urandom(16)
        params = KDFParams(salt=salt)

        params_dict = params.to_dict()

        self.assertIsInstance(params_dict, dict)
        self.assertIn('time_cost', params_dict)
        self.assertIn('memory_cost', params_dict)
        self.assertIn('parallelism', params_dict)
        self.assertIn('salt', params_dict)
        self.assertIn('hash_len', params_dict)

        # Le salt doit être converti en hex
        self.assertIsInstance(params_dict['salt'], str)
        self.assertEqual(params_dict['salt'], salt.hex())

    def test_kdf_params_from_dict(self):
        """Test de création KDFParams depuis un dictionnaire"""
        salt = os.urandom(16)
        params_dict = {
            'time_cost': 3,
            'memory_cost': 512*1024,
            'parallelism': 8,
            'salt': salt.hex(),
            'hash_len': 64
        }

        params = KDFParams.from_dict(params_dict)

        self.assertEqual(params.time_cost, 3)
        self.assertEqual(params.memory_cost, 512*1024)
        self.assertEqual(params.parallelism, 8)
        self.assertEqual(params.salt, salt)
        self.assertEqual(params.hash_len, 64)


class TestKeyDerivation(unittest.TestCase):
    """Tests pour la dérivation de clés"""

    def test_derive_key_with_params(self):
        """Test de dérivation de clé avec paramètres fournis"""
        password = "test_password_123"
        salt = os.urandom(16)
        params = KDFParams(salt=salt, time_cost=1, memory_cost=64*1024)

        key, returned_params = derive_key(password, params)

        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), params.hash_len)
        self.assertEqual(returned_params.salt, salt)

    def test_derive_key_without_params(self):
        """Test de dérivation de clé sans paramètres (génération automatique)"""
        password = "test_password_456"

        key, params = derive_key(password, None)

        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)  # Longueur par défaut
        self.assertIsInstance(params, KDFParams)
        self.assertEqual(len(params.salt), 16)  # Salt généré automatiquement


class TestKeyring(unittest.TestCase):
    """Tests pour la classe Keyring"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.keyring = Keyring()
        self.password = "test_master_password"
        self.salt = os.urandom(16)
        self.params = KDFParams(salt=self.salt, time_cost=1, memory_cost=64*1024)

    def test_keyring_initial_state(self):
        """Test de l'état initial du keyring"""
        self.assertFalse(self.keyring.is_unlocked())

        with self.assertRaises(RuntimeError):
            self.keyring.get_key()

    def test_keyring_unlock_with_kdf_params(self):
        """Test de déverrouillage avec objet KDFParams"""
        self.keyring.unlock(self.password, self.params)

        self.assertTrue(self.keyring.is_unlocked())
        key = self.keyring.get_key()
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)


class TestAEAD(unittest.TestCase):
    """Tests pour le chiffrement AEAD"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.key = os.urandom(32)  # Clé AES-256
        self.plaintext = b"message secret a chiffrer"
        self.aad = b"donnees_additionnelles"

    def test_encrypt_decrypt_roundtrip(self):
        """Test chiffrement/déchiffrement aller-retour"""
        # Chiffrement
        ciphertext, nonce = aead.encrypt(self.key, self.plaintext, self.aad)

        self.assertIsInstance(ciphertext, bytes)
        self.assertIsInstance(nonce, bytes)
        self.assertNotEqual(ciphertext, self.plaintext)

        # Déchiffrement
        decrypted = aead.decrypt(self.key, nonce, ciphertext, self.aad)

        self.assertEqual(decrypted, self.plaintext)


if __name__ == '__main__':
    unittest.main()

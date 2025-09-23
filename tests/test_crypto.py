import unittest
import os
from crypto.key_derivation import KDFParams, derive_key
from crypto.keyring import Keyring
from crypto import aead


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

    def test_kdf_params_from_dict_with_existing_kdf_params(self):
        """Test que from_dict retourne directement un objet KDFParams existant"""
        salt = os.urandom(16)
        original_params = KDFParams(salt=salt, time_cost=5)

        # Passer un objet KDFParams à from_dict doit le retourner tel quel
        result_params = KDFParams.from_dict(original_params)

        self.assertIs(result_params, original_params)

    def test_roundtrip_conversion(self):
        """Test conversion aller-retour dict -> KDFParams -> dict"""
        salt = os.urandom(16)
        original_params = KDFParams(salt=salt, time_cost=4, memory_cost=128*1024)

        # KDFParams -> dict -> KDFParams
        params_dict = original_params.to_dict()
        reconstructed_params = KDFParams.from_dict(params_dict)

        self.assertEqual(original_params.time_cost, reconstructed_params.time_cost)
        self.assertEqual(original_params.memory_cost, reconstructed_params.memory_cost)
        self.assertEqual(original_params.parallelism, reconstructed_params.parallelism)
        self.assertEqual(original_params.salt, reconstructed_params.salt)
        self.assertEqual(original_params.hash_len, reconstructed_params.hash_len)


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

    def test_derive_key_reproducibility(self):
        """Test que la même entrée produit la même clé"""
        password = "test_password_789"
        salt = os.urandom(16)
        params = KDFParams(salt=salt, time_cost=1, memory_cost=64*1024)

        key1, _ = derive_key(password, params)
        key2, _ = derive_key(password, params)

        self.assertEqual(key1, key2)

    def test_derive_key_different_passwords(self):
        """Test que des mots de passe différents produisent des clés différentes"""
        salt = os.urandom(16)
        params = KDFParams(salt=salt, time_cost=1, memory_cost=64*1024)

        key1, _ = derive_key("password1", params)
        key2, _ = derive_key("password2", params)

        self.assertNotEqual(key1, key2)


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

    def test_keyring_unlock_with_vault_meta_dict(self):
        """Test de déverrouillage avec dictionnaire vault_meta"""
        from crypto.key_derivation import derive_key
        import hashlib

        # Créer un verifier
        key, _ = derive_key(self.password, self.params)
        verifier = hashlib.sha256(key).digest()

        vault_meta = {
            "kdf_params": self.params.to_dict(),
            "verifier": verifier
        }

        self.keyring.unlock(self.password, vault_meta)

        self.assertTrue(self.keyring.is_unlocked())
        unlocked_key = self.keyring.get_key()
        self.assertEqual(unlocked_key, key)

    def test_keyring_unlock_with_wrong_password(self):
        """Test de déverrouillage avec mauvais mot de passe"""
        from crypto.key_derivation import derive_key
        import hashlib

        # Créer un verifier avec le bon mot de passe
        key, _ = derive_key(self.password, self.params)
        verifier = hashlib.sha256(key).digest()

        vault_meta = {
            "kdf_params": self.params.to_dict(),
            "verifier": verifier
        }

        # Essayer avec un mauvais mot de passe
        with self.assertRaises(ValueError):
            self.keyring.unlock("wrong_password", vault_meta)

        self.assertFalse(self.keyring.is_unlocked())

    def test_keyring_lock(self):
        """Test de verrouillage du keyring"""
        self.keyring.unlock(self.password, self.params)
        self.assertTrue(self.keyring.is_unlocked())

        self.keyring.lock()

        self.assertFalse(self.keyring.is_unlocked())
        with self.assertRaises(RuntimeError):
            self.keyring.get_key()


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

    def test_encrypt_different_nonces(self):
        """Test que le chiffrement produit des nonces différents"""
        ct1, nonce1 = aead.encrypt(self.key, self.plaintext, self.aad)
        ct2, nonce2 = aead.encrypt(self.key, self.plaintext, self.aad)

        self.assertNotEqual(nonce1, nonce2)
        # Les textes chiffrés doivent être différents même avec le même plaintext
        self.assertNotEqual(ct1, ct2)

    def test_decrypt_with_wrong_key(self):
        """Test déchiffrement avec mauvaise clé"""
        ciphertext, nonce = aead.encrypt(self.key, self.plaintext, self.aad)
        wrong_key = os.urandom(32)

        with self.assertRaises(Exception):  # Doit lever une exception de déchiffrement
            aead.decrypt(wrong_key, nonce, ciphertext, self.aad)

    def test_decrypt_with_wrong_aad(self):
        """Test déchiffrement avec mauvaises données additionnelles"""
        ciphertext, nonce = aead.encrypt(self.key, self.plaintext, self.aad)
        wrong_aad = b"mauvaises_donnees"

        with self.assertRaises(Exception):  # Doit lever une exception de déchiffrement
            aead.decrypt(self.key, nonce, ciphertext, wrong_aad)

    def test_decrypt_with_modified_ciphertext(self):
        """Test déchiffrement avec texte chiffré modifié"""
        ciphertext, nonce = aead.encrypt(self.key, self.plaintext, self.aad)

        # Modifier un byte du texte chiffré
        modified_ciphertext = bytearray(ciphertext)
        modified_ciphertext[0] ^= 1  # Flip un bit

        with self.assertRaises(Exception):  # Doit lever une exception de déchiffrement
            aead.decrypt(self.key, nonce, bytes(modified_ciphertext), self.aad)


if __name__ == '__main__':
    unittest.main()

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
    """Tests for the KDFParams class and key derivation parameters."""

    def test_kdf_params_creation(self):
        """Test creation of a KDFParams object with custom parameters."""
        salt = os.urandom(16)
        params = KDFParams(
            time_cost=2,
            memory_cost=256 * 1024,
            parallelism=4,
            salt=salt,
            hash_len=32,
        )

        assert params.time_cost == 2
        assert params.memory_cost == 256 * 1024
        assert params.parallelism == 4
        assert params.salt == salt
        assert params.hash_len == 32

    def test_kdf_params_to_dict(self):
        """Test conversion of KDFParams to dictionary for serialization."""
        salt = os.urandom(16)
        params = KDFParams(salt=salt)

        params_dict = params.to_dict()

        assert isinstance(params_dict, dict)
        assert "time_cost" in params_dict
        assert "memory_cost" in params_dict
        assert "parallelism" in params_dict
        assert "salt" in params_dict
        assert "hash_len" in params_dict

        # Salt should be converted to hex string
        assert isinstance(params_dict["salt"], str)
        assert params_dict["salt"] == salt.hex()

    def test_kdf_params_from_dict(self):
        """Test creation of KDFParams from dictionary data."""
        salt = os.urandom(16)
        params_dict = {
            "time_cost": 3,
            "memory_cost": 512 * 1024,
            "parallelism": 8,
            "salt": salt.hex(),
            "hash_len": 64,
        }

        params = KDFParams.from_dict(params_dict)

        assert params.time_cost == 3
        assert params.memory_cost == 512 * 1024
        assert params.parallelism == 8
        assert params.salt == salt
        assert params.hash_len == 64

    def test_kdf_params_from_dict_with_existing_kdf_params(self):
        """Test that from_dict returns existing KDFParams object directly."""
        salt = os.urandom(16)
        original_params = KDFParams(salt=salt, time_cost=5)

        # Passing a KDFParams object to from_dict should return it as-is
        result_params = KDFParams.from_dict(original_params)

        assert result_params is original_params

    def test_roundtrip_conversion(self):
        """Test round-trip conversion: KDFParams -> dict -> KDFParams."""
        salt = os.urandom(16)
        original_params = KDFParams(salt=salt, time_cost=4, memory_cost=128 * 1024)

        # KDFParams -> dict -> KDFParams
        params_dict = original_params.to_dict()
        reconstructed_params = KDFParams.from_dict(params_dict)

        assert original_params.time_cost == reconstructed_params.time_cost
        assert original_params.memory_cost == reconstructed_params.memory_cost
        assert original_params.parallelism == reconstructed_params.parallelism
        assert original_params.salt == reconstructed_params.salt
        assert original_params.hash_len == reconstructed_params.hash_len


class TestKeyDerivation(unittest.TestCase):
    """Tests for cryptographic key derivation functions."""

    def test_derive_key_with_params(self):
        """Test key derivation with provided parameters."""
        password = "test_password_123"  # nosec: test password
        salt = os.urandom(16)
        params = KDFParams(salt=salt, time_cost=1, memory_cost=64 * 1024)

        key, returned_params = derive_key(password, params)

        assert isinstance(key, bytes)
        assert len(key) == params.hash_len
        assert returned_params.salt == salt

    def test_derive_key_without_params(self):
        """Test key derivation without parameters (auto-generation)."""
        password = "test_password_456"  # nosec: test password

        key, params = derive_key(password, None)

        assert isinstance(key, bytes)
        assert len(key) == 32  # Default length
        assert isinstance(params, KDFParams)
        assert len(params.salt) == 16  # Auto-generated salt

    def test_derive_key_reproducibility(self):
        """Test that same input produces same key."""
        password = "test_password_789"  # nosec: test password
        salt = os.urandom(16)
        params = KDFParams(salt=salt, time_cost=1, memory_cost=64 * 1024)

        key1, _ = derive_key(password, params)
        key2, _ = derive_key(password, params)

        assert key1 == key2

    def test_derive_key_different_passwords(self):
        """Test that different passwords produce different keys."""
        salt = os.urandom(16)
        params = KDFParams(salt=salt, time_cost=1, memory_cost=64 * 1024)

        key1, _ = derive_key("password1", params)  # nosec: test password
        key2, _ = derive_key("password2", params)  # nosec: test password

        assert key1 != key2


class TestKeyring(unittest.TestCase):
    """Tests for the Keyring class and key management."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.keyring = Keyring()
        self.password = "test_master_password"  # nosec: test password
        self.salt = os.urandom(16)
        self.params = KDFParams(salt=self.salt, time_cost=1, memory_cost=64 * 1024)

    def test_keyring_initial_state(self):
        """Test initial state of keyring (should be locked)."""
        assert not self.keyring.is_unlocked()

        with self.assertRaises(RuntimeError):
            self.keyring.get_key()

    def test_keyring_unlock_with_kdf_params(self):
        """Test unlocking keyring with KDFParams object."""
        self.keyring.unlock(self.password, self.params)

        assert self.keyring.is_unlocked()
        key = self.keyring.get_key()
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_keyring_unlock_with_vault_meta_dict(self):
        """Test unlocking keyring with vault metadata dictionary."""
        import hashlib

        # Create verifier
        key, _ = derive_key(self.password, self.params)
        verifier = hashlib.sha256(key).digest()

        vault_meta = {"kdf_params": self.params.to_dict(), "verifier": verifier}

        self.keyring.unlock(self.password, vault_meta)

        assert self.keyring.is_unlocked()
        unlocked_key = self.keyring.get_key()
        assert unlocked_key == key

    def test_keyring_unlock_with_wrong_password(self):
        """Test unlocking with incorrect password should fail."""
        import hashlib

        # Create verifier with correct password
        key, _ = derive_key(self.password, self.params)
        verifier = hashlib.sha256(key).digest()

        vault_meta = {"kdf_params": self.params.to_dict(), "verifier": verifier}

        # Try with wrong password
        with self.assertRaises(ValueError):
            self.keyring.unlock("wrong_password", vault_meta)  # nosec: test password

        assert not self.keyring.is_unlocked()

    def test_keyring_lock(self):
        """Test locking keyring clears keys from memory."""
        self.keyring.unlock(self.password, self.params)
        assert self.keyring.is_unlocked()

        self.keyring.lock()

        assert not self.keyring.is_unlocked()
        with self.assertRaises(RuntimeError):
            self.keyring.get_key()


class TestAEAD(unittest.TestCase):
    """Tests for Authenticated Encryption with Associated Data."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.key = os.urandom(32)  # AES-256 key
        self.plaintext = b"secret message to encrypt"
        self.aad = b"additional_authenticated_data"

    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption/decryption round-trip maintains data integrity."""
        # Encryption
        ciphertext, nonce = aead.encrypt(self.key, self.plaintext, self.aad)

        assert isinstance(ciphertext, bytes)
        assert isinstance(nonce, bytes)
        assert ciphertext != self.plaintext

        # Decryption
        decrypted = aead.decrypt(self.key, nonce, ciphertext, self.aad)

        assert decrypted == self.plaintext

    def test_encrypt_different_nonces(self):
        """Test that encryption produces different nonces for security."""
        ct1, nonce1 = aead.encrypt(self.key, self.plaintext, self.aad)
        ct2, nonce2 = aead.encrypt(self.key, self.plaintext, self.aad)

        assert nonce1 != nonce2
        # Ciphertexts should be different even with same plaintext
        assert ct1 != ct2

    def test_decrypt_with_wrong_key(self):
        """Test decryption with wrong key should fail."""
        ciphertext, nonce = aead.encrypt(self.key, self.plaintext, self.aad)
        wrong_key = os.urandom(32)

        with self.assertRaises(Exception):  # Should raise decryption exception
            aead.decrypt(wrong_key, nonce, ciphertext, self.aad)

    def test_decrypt_with_wrong_aad(self):
        """Test decryption with wrong associated data should fail."""
        ciphertext, nonce = aead.encrypt(self.key, self.plaintext, self.aad)
        wrong_aad = b"wrong_data"

        with self.assertRaises(Exception):  # Should raise decryption exception
            aead.decrypt(self.key, nonce, ciphertext, wrong_aad)

    def test_decrypt_with_modified_ciphertext(self):
        """Test decryption with tampered ciphertext should fail."""
        ciphertext, nonce = aead.encrypt(self.key, self.plaintext, self.aad)

        # Modify one byte of ciphertext
        modified_ciphertext = bytearray(ciphertext)
        modified_ciphertext[0] ^= 1  # Flip one bit

        with self.assertRaises(Exception):  # Should raise decryption exception
            aead.decrypt(self.key, nonce, bytes(modified_ciphertext), self.aad)


if __name__ == "__main__":
    unittest.main()

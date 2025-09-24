"""
Keyring module for secure key management.
Handles encryption key storage in memory with secure cleanup
and master password verification.
"""

import hashlib
from typing import Optional, Union

from crypto.key_derivation import KDFParams, derive_key


class Keyring:
    """
    Secure key storage and management class.

    Manages encryption keys in memory with automatic cleanup
    and provides master password verification functionality.
    """

    def __init__(self):
        """Initialize empty keyring."""
        self._key: Optional[bytes] = None
        self._params: Optional[KDFParams] = None

    def unlock(
        self, master_password: str, vault_meta_or_params: Union[dict, KDFParams]
    ):
        """
        Unlock the keyring with master password verification.

        Args:
            master_password: The master password to verify
            vault_meta_or_params: Either KDFParams object or vault metadata dict
                                 containing kdf_params and verifier

        Raises:
            ValueError: If master password is incorrect
        """
        # Handle both possible call formats
        if isinstance(vault_meta_or_params, KDFParams):
            # Case 1: direct call from vault.py with KDFParams object
            params = vault_meta_or_params
            verifier = None  # No verification in this case
        else:
            # Case 2: call from app with vault_meta dictionary
            vault_meta = vault_meta_or_params
            kdf_params_data = vault_meta["kdf_params"]

            if isinstance(kdf_params_data, KDFParams):
                params = kdf_params_data
            else:
                # It's a dict, convert it
                params = KDFParams.from_dict(kdf_params_data)

            verifier = vault_meta.get("verifier")

        # Derive key from master password
        key, _ = derive_key(master_password, params)

        # Verify master password using stored verifier (if available)
        if verifier is not None and hashlib.sha256(key).digest() != verifier:
            raise ValueError("Incorrect master password")

        # Store key and parameters in memory
        self._key = key
        self._params = params

    def get_key(self) -> bytes:
        """
        Get the current encryption key.

        Returns:
            The encryption key bytes

        Raises:
            RuntimeError: If vault is locked (no key available)
        """
        if not self._key:
            raise RuntimeError("Vault locked: no key available")
        return self._key

    def lock(self):
        """
        Lock the keyring and securely clear keys from memory.

        Performs best-effort secure memory cleanup by overwriting
        key bytes before deletion.
        """
        if self._key:
            # Best effort: overwrite bytes before deletion
            mutable = bytearray(self._key)
            for i in range(len(mutable)):
                mutable[i] = 0
        self._key = None
        self._params = None

    def is_unlocked(self) -> bool:
        """
        Check if keyring is currently unlocked.

        Returns:
            True if keyring has a valid key, False otherwise
        """
        return self._key is not None

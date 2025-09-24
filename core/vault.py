"""
Core vault module for the password manager.
Handles the main vault operations including initialization, password management,
and secure storage/retrieval of entries.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

from core import generator
from core.generator import StrengthResult, validate_password_strength
from crypto import aead
from crypto.key_derivation import derive_key
from crypto.keyring import Keyring
from storage import repository, schema
from storage.repository import Entry


class Vault:
    """
    Main class for managing the password vault.

    Provides secure storage and retrieval of password entries with
    master password protection and automatic encryption/decryption.
    """

    def __init__(self, db_path: Path):
        """
        Initialize a new vault instance.

        Args:
            db_path: Path to the SQLite database file
        """
        self.con = schema.open_db(db_path)
        self._keyring = Keyring()

    def validate_master_password(self, password: str) -> StrengthResult:
        """
        Validate master password strength using security criteria.

        Args:
            password: The master password to validate

        Returns:
            StrengthResult indicating if password meets requirements
        """
        return validate_password_strength(
            password,
            min_length=12,
            require_types=4,  # Require all types: upper, lower, digits, special
        )

    def init_master_password(self, master_password: str):
        """
        Initialize the vault with a strong master password.
        Checks password strength and creates vault_meta in the database.

        Args:
            master_password: The master password to use for encryption

        Raises:
            RuntimeError: If vault is already initialized
            ValueError: If master password is too weak
        """
        # Check if vault is already initialized
        meta = repository.load_vault_meta(self.con)
        if meta:
            raise RuntimeError("Vault already initialized")

        # Validate master password strength
        result = self.validate_master_password(master_password)
        if not result.ok:
            raise ValueError(
                "Master password too weak: " + "; ".join(result.reasons)
            )

        # Derive key using Argon2
        key, params = derive_key(master_password, None)

        # Store key hash in database for future verification
        verifier = hashlib.sha256(key).digest()
        repository.save_vault_meta(
            self.con,
            {
                "kdf_name": "argon2id",
                "kdf_params": params.to_dict(),
                "salt": params.salt,
                "verifier": verifier,
                "version": 1,
            },
        )

        # Unlock the vault with the keyring
        self._keyring.unlock(master_password, params)

    def add_entry(
        self,
        url: str,
        title: str | None,
        username: str | None,
        password: str,
        master_password: str | None = None,
        auto_lock: bool = True,
    ) -> int:
        """
        Add a new entry to the vault.

        Args:
            url: Service URL
            title: Entry title (optional, uses URL as default)
            username: Username (optional)
            password: Password to store
            master_password: Master password to unlock if needed
            auto_lock: If True, re-lock vault after adding

        Returns:
            The ID of the new entry

        Raises:
            AssertionError: If vault is locked and no master_password provided
            ValueError: If unable to unlock vault
        """
        was_locked = not self._keyring.is_unlocked()

        # If vault is locked, attempt to unlock it
        if was_locked:
            if not master_password:
                raise AssertionError(
                    "Vault locked: provide master_password to unlock automatically"
                )

            try:
                self.unlock(master_password)
            except Exception as e:
                raise ValueError(f"Unable to unlock vault: {e}") from e

        try:
            # Add the entry
            key = self._keyring.get_key()
            # Convert password to bytes
            plaintext = password.encode("utf-8")
            # Encrypt the password
            ct, nonce = aead.encrypt(key, plaintext, aad=url.encode("utf-8"))
            entry = Entry(
                id=None,
                url=url,
                title=title or url,  # If title missing, use URL as title
                username=username,
                password_ct=ct,
                nonce=nonce,
            )
            return repository.add_entry(self.con, entry)

        finally:
            # Re-lock vault if it was locked before and auto_lock is enabled
            if was_locked and auto_lock:
                self.lock()

    def get_entry(self, entry_id: int, reveal: bool = False) -> Entry | None:
        """
        Retrieve an entry by its ID.

        Args:
            entry_id: The entry ID to retrieve
            reveal: If True, decrypt and reveal the password in plaintext

        Returns:
            The entry if found, None otherwise

        Raises:
            AssertionError: If vault is locked and reveal=True
        """
        entry = repository.get_entry(self.con, entry_id)
        if entry and reveal:
            if not self._keyring.is_unlocked():
                raise AssertionError("Vault locked")
            key = self._keyring.get_key()
            clear = aead.decrypt(
                key, entry.nonce, entry.password_ct, aad=entry.url.encode("utf-8")
            )
            entry.password_ct = clear.decode("utf-8")
        return entry

    def search(self, query: str) -> Iterable[Entry]:
        """
        Search entries by URL, title or username.

        Args:
            query: Search query string

        Returns:
            Iterable of matching entries
        """
        return repository.search(self.con, query)

    def delete(self, entry_id: int) -> bool:
        """
        Delete an entry by its ID.

        Args:
            entry_id: The ID of the entry to delete

        Returns:
            True if entry was deleted, False if not found
        """
        return repository.delete(self.con, entry_id)

    def lock(self):
        """Lock the vault by clearing the keyring."""
        self._keyring.lock()

    def unlock(self, master_password: str):
        """
        Unlock the vault with the master password.

        Args:
            master_password: The master password to unlock with

        Raises:
            RuntimeError: If vault is not initialized
            ValueError: If master password is incorrect
        """
        # Load vault metadata
        meta = repository.load_vault_meta(self.con)
        if not meta:
            msg = "Vault not initialized. Call init_master_password() first."
            raise RuntimeError(msg)

        # Unlock keyring with stored metadata
        self._keyring.unlock(master_password, meta)

    def is_unlocked(self) -> bool:
        """
        Check if the vault is currently unlocked.

        Returns:
            True if vault is unlocked, False otherwise
        """
        return self._keyring.is_unlocked()

    def list_passwords(self) -> list[Entry]:
        """
        List all entries in the vault.

        Returns:
            List of all vault entries (passwords remain encrypted)
        """
        return repository.list_entries(self.con)

    # ---------- Password Generation ----------
    def generate_password(
        self,
        length: int = 16,
        use_digits: bool = True,
        use_specials: bool = True,
        use_upper: bool = True,
        use_lower: bool = True,
    ) -> str:
        """
        Generate a strong password using core.generator.

        Args:
            length: Password length
            use_digits: Include digits
            use_specials: Include special characters
            use_upper: Include uppercase letters
            use_lower: Include lowercase letters

        Returns:
            Generated password string
        """
        return generator.generate_password(
            length=length,
            use_digits=use_digits,
            use_specials=use_specials,
            use_upper=use_upper,
            use_lower=use_lower,
        )

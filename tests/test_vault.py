"""
Comprehensive tests for vault functionality.
Tests vault initialization, password management, encryption,
persistence, and security isolation features.
"""

import os
import tempfile
import unittest
from pathlib import Path

from core.vault import Vault
from crypto.key_derivation import KDFParams
from storage import repository
from storage.repository import Entry


class TestVault(unittest.TestCase):
    """Tests for the main Vault class functionality."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Create temporary database file for testing
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.test_db_fd)  # Close file descriptor

        self.vault = Vault(Path(self.test_db_path))
        self.master_password = "TestMasterPassword123!"  # nosec: test password

    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary database file
        test_path = Path(self.test_db_path)
        if test_path.exists():
            test_path.unlink()

    def test_vault_initialization(self):
        """Test vault initialization without errors."""
        # Vault should be created without error
        assert self.vault is not None
        assert self.vault.con is not None

    def test_init_master_password_strong(self):
        """Test initialization with a strong master password."""
        strong_password = "MyVeryStr0ng!MasterP@ssw0rd2024"  # nosec: test password

        # Initialization should succeed
        self.vault.init_master_password(strong_password)

        # Verify metadata was saved
        meta = repository.load_vault_meta(self.vault.con)
        assert meta is not None
        assert "kdf_params" in meta
        assert "verifier" in meta
        assert "version" in meta

    def test_init_master_password_weak(self):
        """Test initialization with weak password should fail."""
        weak_password = "123"  # nosec: test password

        # Initialization should fail
        with self.assertRaises(ValueError):
            self.vault.init_master_password(weak_password)

    def test_init_master_password_already_initialized(self):
        """Test initialization on already initialized vault should fail."""
        # Initialize first time
        self.vault.init_master_password(self.master_password)

        # Trying to initialize again should fail
        with self.assertRaises(RuntimeError):
            self.vault.init_master_password("AnotherPassword123!")  # nosec: test password

    def test_add_entry_vault_locked(self):
        """Test adding entry with locked vault should fail."""
        # Vault is not unlocked
        with self.assertRaises(AssertionError):
            self.vault.add_entry(
                url="https://example.com",
                title="Test Entry",
                username="testuser",
                password="testpass",  # nosec: test password
            )

    def test_add_entry_vault_unlocked(self):
        """Test adding entry with unlocked vault."""
        # Initialize and unlock vault
        self.vault.init_master_password(self.master_password)

        # Add an entry
        entry_id = self.vault.add_entry(
            url="https://example.com",
            title="Test Entry",
            username="testuser",
            password="testpass123",  # nosec: test password
        )

        assert isinstance(entry_id, int)
        assert entry_id > 0

    def test_get_entry_without_reveal(self):
        """Test retrieving entry without revealing password."""
        # Initialize vault and add entry
        self.vault.init_master_password(self.master_password)
        entry_id = self.vault.add_entry(
            url="https://test.com",
            title="Test Site",
            username="user@test.com",
            password="secretpassword",  # nosec: test password
        )

        # Retrieve entry without revealing password
        entry = self.vault.get_entry(entry_id, reveal=False)

        assert entry is not None
        assert entry.url == "https://test.com"
        assert entry.title == "Test Site"
        assert entry.username == "user@test.com"
        # Password should be encrypted (bytes)
        assert isinstance(entry.password_ct, bytes)

    def test_get_entry_with_reveal(self):
        """Test retrieving entry with password revelation."""
        # Initialize vault and add entry
        self.vault.init_master_password(self.master_password)
        original_password = "secretpassword123"  # nosec: test password
        entry_id = self.vault.add_entry(
            url="https://test.com",
            title="Test Site",
            username="user@test.com",
            password=original_password,
        )

        # Retrieve entry with password revelation
        entry = self.vault.get_entry(entry_id, reveal=True)

        assert entry is not None
        assert entry.password_ct == original_password

    def test_search_entries(self):
        """Test searching vault entries."""
        # Initialize vault and add multiple entries
        self.vault.init_master_password(self.master_password)

        # Add test entries
        self.vault.add_entry("https://google.com", "Google", "user@gmail.com", "pass1")  # nosec: test password
        self.vault.add_entry("https://github.com", "GitHub", "developer", "pass2")  # nosec: test password
        self.vault.add_entry("https://stackoverflow.com", "Stack Overflow", "coder", "pass3")  # nosec: test password

        # Search by URL
        results = list(self.vault.search("google"))
        assert len(results) == 1
        assert results[0].url == "https://google.com"

        # Search by username
        results = list(self.vault.search("developer"))
        assert len(results) == 1
        assert results[0].username == "developer"

        # Search by title
        results = list(self.vault.search("Stack"))
        assert len(results) == 1
        assert results[0].title == "Stack Overflow"

        # Search with no results
        results = list(self.vault.search("nonexistent"))
        assert len(results) == 0


class TestVaultIntegration(unittest.TestCase):
    """Integration tests for vault functionality."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.test_db_fd)
        self.vault = Vault(Path(self.test_db_path))
        self.master_password = "IntegrationTest123!"  # nosec: test password

    def tearDown(self):
        """Clean up after each test."""
        test_path = Path(self.test_db_path)
        if test_path.exists():
            test_path.unlink()

    def test_full_workflow(self):
        """Test complete vault workflow from initialization to search."""
        # 1. Initialize vault
        self.vault.init_master_password(self.master_password)

        # 2. Add multiple entries
        entries_data = [
            ("https://bank.com", "My Bank", "account123", "bankpass123"),  # nosec: test password
            ("https://email.com", "Email Provider", "user@email.com", "emailpass456"),  # nosec: test password
            ("https://work.com", "Work Portal", "employee", "workpass789"),  # nosec: test password
        ]

        entry_ids = []
        for url, title, username, password in entries_data:
            entry_id = self.vault.add_entry(url, title, username, password)
            entry_ids.append(entry_id)

        # 3. Verify all entries were added
        assert len(entry_ids) == 3

        # 4. Search and verify entries
        for i, (url, title, username, password) in enumerate(entries_data):
            entry = self.vault.get_entry(entry_ids[i], reveal=True)
            assert entry.url == url
            assert entry.title == title
            assert entry.username == username
            assert entry.password_ct == password

        # 5. Test search functionality
        bank_results = list(self.vault.search("bank"))
        assert len(bank_results) == 1
        assert bank_results[0].title == "My Bank"

        # 6. Lock and attempt access (should fail)
        self.vault._keyring.lock()
        with self.assertRaises(AssertionError):
            self.vault.get_entry(entry_ids[0], reveal=True)

    def test_vault_security_isolation(self):
        """Test security isolation between different vaults."""
        # Create second vault
        vault2_fd, vault2_path = tempfile.mkstemp(suffix=".db")
        os.close(vault2_fd)

        try:
            vault2 = Vault(Path(vault2_path))

            # Initialize both vaults with different passwords
            self.vault.init_master_password("Password1!")  # nosec: test password
            vault2.init_master_password("Password2!")  # nosec: test password

            # Add different entries
            same_password = "samepassword"  # nosec: test password
            id1 = self.vault.add_entry("https://vault1.com", "Vault 1", "user1", same_password)
            id2 = vault2.add_entry("https://vault2.com", "Vault 2", "user2", same_password)

            # Each vault can only access its own data
            entry1 = self.vault.get_entry(id1, reveal=True)
            entry2 = vault2.get_entry(id2, reveal=True)

            assert entry1.password_ct == same_password
            assert entry2.password_ct == same_password

            # Encrypted data should be different
            vault1_entry = repository.get_entry(self.vault.con, id1)
            vault2_entry = repository.get_entry(vault2.con, id2)

            # Encrypted data should be different even with same password
            if id1 == id2:  # If same ID
                assert vault1_entry.password_ct != vault2_entry.password_ct

        finally:
            # Clean up second vault
            vault2_path = Path(vault2_path)
            if vault2_path.exists():
                vault2_path.unlink()


if __name__ == "__main__":
    unittest.main()

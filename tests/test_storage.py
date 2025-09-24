"""
Comprehensive tests for storage and database functionality.
Tests repository operations, schema management, and data persistence
to ensure reliable and secure data storage.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from storage import repository, schema
from storage.repository import Entry


class TestRepository(unittest.TestCase):
    """Tests for database repository operations."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.test_db_fd)
        self.con = schema.open_db(Path(self.test_db_path))

    def tearDown(self):
        """Clean up after each test."""
        self.con.close()
        test_path = Path(self.test_db_path)
        if test_path.exists():
            test_path.unlink()

    def test_add_entry(self):
        """Test adding password entry to database."""
        entry = Entry(
            id=None,
            url="https://test.com",
            title="Test Site",
            username="testuser",
            password_ct=b"encrypted_password",
            nonce=b"test_nonce",
        )

        entry_id = repository.add_entry(self.con, entry)

        assert isinstance(entry_id, int)
        assert entry_id > 0

    def test_get_entry(self):
        """Test retrieving password entry by ID."""
        # Add entry first
        entry = Entry(
            id=None,
            url="https://example.com",
            title="Example",
            username="user",
            password_ct=b"secret",
            nonce=b"nonce123",
        )
        entry_id = repository.add_entry(self.con, entry)

        # Retrieve the entry
        retrieved_entry = repository.get_entry(self.con, entry_id)

        assert retrieved_entry is not None
        assert retrieved_entry.id == entry_id
        assert retrieved_entry.url == "https://example.com"
        assert retrieved_entry.title == "Example"
        assert retrieved_entry.username == "user"
        assert retrieved_entry.password_ct == b"secret"
        assert retrieved_entry.nonce == b"nonce123"

    def test_get_nonexistent_entry(self):
        """Test retrieving nonexistent entry returns None."""
        entry = repository.get_entry(self.con, 999999)
        assert entry is None

    def test_search_entries(self):
        """Test searching password entries by various fields."""
        # Add multiple entries
        entries_data = [
            ("https://google.com", "Google Search", "user@gmail.com"),
            ("https://github.com", "GitHub", "developer"),
            ("https://stackoverflow.com", "Stack Overflow", "coder"),
        ]

        for url, title, username in entries_data:
            entry = Entry(
                id=None,
                url=url,
                title=title,
                username=username,
                password_ct=b"password",
                nonce=b"nonce",
            )
            repository.add_entry(self.con, entry)

        # Test search by URL
        results = list(repository.search(self.con, "google"))
        assert len(results) == 1
        assert results[0].url == "https://google.com"

        # Test search by title
        results = list(repository.search(self.con, "GitHub"))
        assert len(results) == 1
        assert results[0].title == "GitHub"

        # Test search by username
        results = list(repository.search(self.con, "developer"))
        assert len(results) == 1
        assert results[0].username == "developer"

        # Test partial search
        results = list(repository.search(self.con, "stack"))
        assert len(results) == 1
        assert results[0].title == "Stack Overflow"

        # Test search with no results
        results = list(repository.search(self.con, "nonexistent"))
        assert len(results) == 0

    def test_delete_entry(self):
        """Test deleting password entry."""
        # Add entry
        entry = Entry(
            id=None,
            url="https://todelete.com",
            title="To Delete",
            username="user",
            password_ct=b"password",
            nonce=b"nonce",
        )
        entry_id = repository.add_entry(self.con, entry)

        # Verify it exists
        assert repository.get_entry(self.con, entry_id) is not None

        # Delete the entry
        result = repository.delete(self.con, entry_id)
        assert result is True

        # Verify it no longer exists
        assert repository.get_entry(self.con, entry_id) is None

    def test_save_vault_meta(self):
        """Test saving vault metadata to database."""
        meta = {
            "kdf_name": "argon2",
            "kdf_params": {
                "time_cost": 2,
                "memory_cost": 256 * 1024,
                "parallelism": 4,
                "salt": "abcd1234",
                "hash_len": 32,
            },
            "salt": b"test_salt",
            "verifier": b"test_verifier",
            "version": 1,
        }

        repository.save_vault_meta(self.con, meta)

        # Verify data was saved
        loaded_meta = repository.load_vault_meta(self.con)
        assert loaded_meta is not None
        assert loaded_meta["kdf_name"] == "argon2"
        assert loaded_meta["version"] == 1
        assert loaded_meta["salt"] == b"test_salt"
        assert loaded_meta["verifier"] == b"test_verifier"

        # Verify kdf_params was serialized/deserialized correctly
        kdf_params = loaded_meta["kdf_params"]
        assert isinstance(kdf_params, dict)
        assert kdf_params["time_cost"] == 2
        assert kdf_params["memory_cost"] == 256 * 1024


class TestSchema(unittest.TestCase):
    """Tests for database schema management."""

    def test_open_new_db(self):
        """Test opening a new database creates proper schema."""
        test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
        os.close(test_db_fd)
        Path(test_db_path).unlink()  # Remove file to test creation

        try:
            con = schema.open_db(Path(test_db_path))

            # Verify connection is valid
            assert con is not None

            # Verify tables were created
            cursor = con.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "entries" in tables
            assert "vault_meta" in tables

            con.close()

        finally:
            test_path = Path(test_db_path)
            if test_path.exists():
                test_path.unlink()

    def test_db_schema_structure(self):
        """Test database schema structure is correct."""
        test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
        os.close(test_db_fd)

        try:
            con = schema.open_db(Path(test_db_path))

            # Verify entries table structure
            cursor = con.execute("PRAGMA table_info(entries)")
            entries_columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_entries_columns = {
                "id": "INTEGER",
                "url": "TEXT",
                "title": "TEXT",
                "username": "TEXT",
                "password_ct": "BLOB",
                "nonce": "BLOB",
                "created_at": "TEXT",
                "updated_at": "TEXT",
            }

            for col_name, col_type in expected_entries_columns.items():
                assert col_name in entries_columns
                assert entries_columns[col_name] == col_type

            # Verify vault_meta table structure
            cursor = con.execute("PRAGMA table_info(vault_meta)")
            meta_columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_meta_columns = {
                "kdf_name": "TEXT",
                "kdf_params": "TEXT",
                "salt": "BLOB",
                "verifier": "BLOB",
                "version": "INTEGER",
            }

            for col_name, col_type in expected_meta_columns.items():
                assert col_name in meta_columns
                assert meta_columns[col_name] == col_type

            con.close()

        finally:
            test_path = Path(test_db_path)
            if test_path.exists():
                test_path.unlink()


class TestRepositoryIntegration(unittest.TestCase):
    """Integration tests for storage functionality."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.test_db_fd)
        self.con = schema.open_db(Path(self.test_db_path))

    def tearDown(self):
        """Clean up after each test."""
        self.con.close()
        test_path = Path(self.test_db_path)
        if test_path.exists():
            test_path.unlink()

    def test_full_storage_workflow(self):
        """Test complete storage workflow with metadata and entries."""
        # 1. Save vault metadata
        meta = {
            "kdf_name": "argon2",
            "kdf_params": {"time_cost": 2, "memory_cost": 65536},
            "salt": b"test_salt_123",
            "verifier": b"test_verifier_456",
            "version": 1,
        }
        repository.save_vault_meta(self.con, meta)

        # 2. Add multiple entries
        entries_data = [
            ("https://site1.com", "Site 1", "user1", b"pass1", b"nonce1"),
            ("https://site2.com", "Site 2", "user2", b"pass2", b"nonce2"),
            ("https://site3.com", "Site 3", "user3", b"pass3", b"nonce3"),
        ]

        entry_ids = []
        for url, title, username, password_ct, nonce in entries_data:
            entry = Entry(
                id=None,
                url=url,
                title=title,
                username=username,
                password_ct=password_ct,
                nonce=nonce,
            )
            entry_id = repository.add_entry(self.con, entry)
            entry_ids.append(entry_id)

        # 3. Verify metadata is retrievable
        loaded_meta = repository.load_vault_meta(self.con)
        assert loaded_meta["kdf_name"] == "argon2"
        assert loaded_meta["version"] == 1

        # 4. Verify all entries are retrievable
        all_entries = repository.list_entries(self.con)
        assert len(all_entries) == 3

        # 5. Test search functionality
        site1_results = list(repository.search(self.con, "Site 1"))
        assert len(site1_results) == 1
        assert site1_results[0].title == "Site 1"

        # 6. Delete an entry
        repository.delete(self.con, entry_ids[0])
        remaining_entries = repository.list_entries(self.con)
        assert len(remaining_entries) == 2

        # 7. Verify deleted entry no longer exists
        deleted_entry = repository.get_entry(self.con, entry_ids[0])
        assert deleted_entry is None


if __name__ == "__main__":
    unittest.main()

"""
Database schema module for the password manager.
Handles SQLite database initialization and schema creation
with optimized indexing and WAL mode for better performance.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def open_db(path: Path | str) -> sqlite3.Connection:
    """
    Open or create a SQLite database with the password manager schema.

    Args:
        path: Path to the database file (created if doesn't exist)

    Returns:
        SQLite connection with schema initialized

    Note:
        Automatically creates parent directories if they don't exist.
        Enables WAL mode for better concurrent access performance.
    """
    path = Path(path)  # Ensure path is a Path object
    path.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories

    # Connect to database and initialize schema
    con = sqlite3.connect(str(path))
    con.executescript(SCHEMA)
    return con


# Database schema definition
SCHEMA = r"""
-- Enable WAL mode for better performance and concurrent access
PRAGMA journal_mode=WAL;

-- Main entries table for storing encrypted password data
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,                          -- Service URL
    title TEXT,                                 -- Human-readable service name
    username TEXT,                              -- Username for the service
    password_ct BLOB NOT NULL,                  -- Encrypted password
    nonce BLOB NOT NULL,                        -- Encryption nonce
    created_at TEXT DEFAULT (datetime('now')),  -- Entry creation timestamp
    updated_at TEXT DEFAULT (datetime('now'))   -- Last modification timestamp
);

-- Index for faster URL-based lookups
CREATE INDEX IF NOT EXISTS idx_entries_url
    ON entries(url);

-- Vault metadata table (should contain only one row)
CREATE TABLE IF NOT EXISTS vault_meta (
    kdf_name TEXT,                              -- Key derivation function name
    kdf_params TEXT,                            -- KDF parameters as JSON
    salt BLOB,                                  -- Salt for key derivation
    verifier BLOB,                              -- Hash for password verification
    created_at TEXT DEFAULT (datetime('now')), -- Vault creation timestamp
    version INTEGER                             -- Vault format version
);
"""

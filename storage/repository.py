"""
Database repository module for password manager.
Handles all database operations including entry management,
vault metadata storage, and search functionality.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class Entry:
    """
    Password entry data structure.

    Attributes:
        id: Unique entry identifier (None for new entries)
        url: Service URL
        title: Entry title/service name
        username: Username for the service
        password_ct: Encrypted password bytes
        nonce: Encryption nonce bytes
    """

    id: int | None
    url: str
    title: str | None
    username: str | None
    password_ct: bytes
    nonce: bytes


def add_entry(con: sqlite3.Connection, entry: Entry) -> int:
    """
    Add a new password entry to the database.

    Args:
        con: Database connection
        entry: Entry object to add (id should be None)

    Returns:
        The ID of the newly created entry
    """
    cur = con.execute(
        """
        INSERT INTO entries(url, title, username, password_ct, nonce)
        VALUES (?, ?, ?, ?, ?)
        """,
        (entry.url, entry.title, entry.username, entry.password_ct, entry.nonce),
    )
    con.commit()
    return cur.lastrowid


def get_entry(con: sqlite3.Connection, entry_id: int) -> Entry | None:
    """
    Retrieve a password entry by its ID.

    Args:
        con: Database connection
        entry_id: The entry ID to retrieve

    Returns:
        Entry object if found, None otherwise
    """
    row = con.execute(
        """
        SELECT id, url, title, username, password_ct, nonce
        FROM entries
        WHERE id = ?
        """,
        (entry_id,),
    ).fetchone()

    if not row:
        return None

    return Entry(*row)


def search(con: sqlite3.Connection, query: str) -> Iterable[Entry]:
    """
    Search password entries by URL, title, or username.

    Args:
        con: Database connection
        query: Search query string (case-insensitive)

    Yields:
        Entry objects matching the search query
    """
    rows = con.execute(
        """
        SELECT id, url, title, username, password_ct, nonce
        FROM entries
        WHERE url LIKE ? OR title LIKE ? OR username LIKE ?
        ORDER BY updated_at DESC
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%"),
    ).fetchall()

    for row in rows:
        yield Entry(*row)


def delete(con: sqlite3.Connection, entry_id: int) -> bool:
    """
    Delete a password entry by its ID.

    Args:
        con: Database connection
        entry_id: The entry ID to delete

    Returns:
        True if entry was deleted, False if not found
    """
    cur = con.execute(
        """
        DELETE FROM entries
        WHERE id = ?
        """,
        (entry_id,),
    )
    con.commit()
    return cur.rowcount > 0


def save_vault_meta(con: sqlite3.Connection, meta: dict) -> None:
    """
    Save vault metadata to the database.

    Replaces any existing metadata (only one vault per database).

    Args:
        con: Database connection
        meta: Vault metadata dictionary containing:
              - kdf_name: Name of key derivation function
              - kdf_params: KDF parameters as dict
              - salt: Salt bytes for key derivation
              - verifier: Hash for master password verification
              - version: Vault format version
    """
    # Remove any existing metadata (only one vault per database)
    con.execute("DELETE FROM vault_meta")

    # Insert new metadata
    con.execute(
        """
        INSERT INTO vault_meta(kdf_name, kdf_params, salt, verifier, version)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            meta["kdf_name"],
            json.dumps(meta["kdf_params"]),  # Serialize KDF params as JSON
            meta["salt"],
            meta["verifier"],
            meta["version"],
        ),
    )
    con.commit()


def load_vault_meta(con: sqlite3.Connection) -> dict | None:
    """
    Load vault metadata from the database.

    Args:
        con: Database connection

    Returns:
        Vault metadata dictionary if found, None if vault not initialized
    """
    row = con.execute(
        """
        SELECT kdf_name, kdf_params, salt, verifier, version
        FROM vault_meta
        """
    ).fetchone()

    if not row:
        return None

    kdf_name, kdf_params, salt, verifier, version = row
    return {
        "kdf_name": kdf_name,
        "kdf_params": json.loads(kdf_params),  # Deserialize KDF params from JSON
        "salt": salt,
        "verifier": verifier,
        "version": version,
    }


def list_entries(con: sqlite3.Connection) -> list[Entry]:
    """
    Retrieve all vault entries, sorted by modification date.

    Args:
        con: Database connection

    Returns:
        List of all entries, newest first
    """
    rows = con.execute(
        """
        SELECT id, url, title, username, password_ct, nonce
        FROM entries
        ORDER BY updated_at DESC
        """
    ).fetchall()
    return [Entry(*row) for row in rows]

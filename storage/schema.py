import sqlite3
from pathlib import Path
from typing import Optional, Union

def open_db(path: Union[Path, str]) -> sqlite3.Connection:
    path = Path(path)                 # ✅ coercition
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    # ... exécuter le SCHEMA ...
    return con

SCHEMA = r"""
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    username TEXT,
    password_ct BLOB NOT NULL,
    nonce BLOB NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_entries_url
    ON entries(url);

CREATE TABLE IF NOT EXISTS vault_meta (
    kdf_name TEXT,
    kdf_params TEXT,
    salt BLOB,
    verifier BLOB,
    created_at TEXT DEFAULT (datetime('now')),
    version INTEGER
);
"""


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.executescript(SCHEMA)
    return con
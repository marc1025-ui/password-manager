"""
Module de schéma de base de données pour le gestionnaire de mots de passe.
Gère l'initialisation de la base de données SQLite et la création de schémas
avec un index optimisé et le mode WAL pour de meilleures performances.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Union


def open_db(path: Union[Path, str]) -> sqlite3.Connection:
    """
    Ouvrir ou créer une base de données SQLite avec le schéma du gestionnaire de mots de passe.

    Args:
        path: Chemin vers le fichier de base de données (créé s'il n'existe pas)

    Returns:
        Connexion SQLite avec le schéma initialisé

    Note:
        Crée automatiquement les répertoires parents s'ils n'existent pas.
        Active le mode WAL pour de meilleures performances d'accès concurrent.
    """
    path = Path(path)  # ✅ coercition
    path.parent.mkdir(parents=True, exist_ok=True)  # Créer des répertoires parents
    con = sqlite3.connect(str(path))
    con.executescript(SCHEMA)
    return con


# Définition du schéma de base de données avec la colonne username incluse
SCHEMA = r"""
-- Activer le mode WAL pour de meilleures performances et un accès concurrent
PRAGMA journal_mode=WAL;

-- Table principale des entrées pour stocker les données de mot de passe chiffrées
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,                          -- URL du service
    title TEXT,                                 -- Nom du service lisible par l'homme
    username TEXT,                              -- Nom d'utilisateur pour le service
    password_ct BLOB NOT NULL,                  -- Mot de passe chiffré
    nonce BLOB NOT NULL,                        -- Nonce de chiffrement
    created_at TEXT DEFAULT (datetime('now')),  -- Horodatage de création de l'entrée
    updated_at TEXT DEFAULT (datetime('now'))   -- Horodatage de la dernière modification
);

-- Index pour des recherches plus rapides basées sur l'URL
CREATE INDEX IF NOT EXISTS idx_entries_url
    ON entries(url);

-- Table des métadonnées du coffre-fort avec colonne username incluse
CREATE TABLE IF NOT EXISTS vault_meta (
    kdf_name TEXT,                              -- Nom de la fonction de dérivation de clé
    kdf_params TEXT,                            -- Paramètres de la KDF au format JSON
    salt BLOB,                                  -- Sel pour la dérivation de clé
    verifier BLOB,                              -- Hachage pour la vérification du mot de passe
    created_at TEXT DEFAULT (datetime('now')), -- Horodatage de création du coffre-fort
    version INTEGER,                             -- Version du format du coffre-fort
    username TEXT DEFAULT ''                    -- Nom d'utilisateur du coffre-fort
);
"""

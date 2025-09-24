"""
Module de référentiel de base de données pour le gestionnaire de mots de passe.
Gère toutes les opérations de base de données, y compris la gestion des entrées,
le stockage des métadonnées du coffre-fort et la fonctionnalité de recherche.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Optional, Iterable
from dataclasses import dataclass


@dataclass
class Entry:
    """
    Structure de données d'entrée de mot de passe.

    Attributs:
        id: Identifiant unique de l'entrée (None pour les nouvelles entrées)
        url: URL du service
        title: Titre de l'entrée / nom du service
        username: Nom d'utilisateur pour le service
        password_ct: Mot de passe chiffré en bytes
        nonce: Bytes de nonce pour le chiffrement
    """

    id: Optional[int]
    url: str
    title: Optional[str]
    username: Optional[str]
    password_ct: bytes
    nonce: bytes


def add_entry(con: sqlite3.Connection, entry: Entry) -> int:
    """
    Ajoute une nouvelle entrée de mot de passe à la base de données.

    Args:
        con: Connexion à la base de données
        entry: Objet Entry à ajouter (id doit être None)

    Returns:
        L'ID de la nouvelle entrée créée
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


def get_entry(con: sqlite3.Connection, entry_id: int) -> Optional[Entry]:
    """
    Récupère une entrée de mot de passe par son ID.

    Args:
        con: Connexion à la base de données
        entry_id: L'ID de l'entrée à récupérer

    Returns:
        Objet Entry si trouvé, None sinon
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
    Recherche des entrées de mots de passe par URL, titre ou nom d'utilisateur.

    Args:
        con: Connexion à la base de données
        query: Chaîne de requête de recherche (insensible à la casse)

    Yields:
        Objets Entry correspondant à la requête de recherche
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
    Supprime une entrée de mot de passe par son ID.

    Args:
        con: Connexion à la base de données
        entry_id: L'ID de l'entrée à supprimer

    Returns:
        True si l'entrée a été supprimée, False si non trouvée
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
    Sauvegarde les métadonnées du coffre-fort dans la base de données.

    Remplace toutes les métadonnées existantes (un seul coffre-fort par base de données).

    Args:
        con: Connexion à la base de données
        meta: Dictionnaire de métadonnées du coffre-fort contenant:
              - kdf_name: Nom de la fonction de dérivation de clé
              - kdf_params: Paramètres de la DDK sous forme de dict
              - salt: Bytes de sel pour la dérivation de clé
              - verifier: Hachage pour la vérification du mot de passe maître
              - version: Version du format du coffre-fort
    """
    # Supprime les métadonnées existantes (un seul coffre-fort par base de données)
    con.execute("DELETE FROM vault_meta")

    # Insère les nouvelles métadonnées
    con.execute(
        """
        INSERT INTO vault_meta(kdf_name, kdf_params, salt, verifier, version)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            meta["kdf_name"],
            json.dumps(meta["kdf_params"]),  # Sérialise les paramètres de la DDK en JSON
            meta["salt"],
            meta["verifier"],
            meta["version"],
        ),
    )
    con.commit()


def load_vault_meta(con: sqlite3.Connection) -> Optional[dict]:
    """
    Charge les métadonnées du coffre-fort depuis la base de données.

    Args:
        con: Connexion à la base de données

    Returns:
        Dictionnaire de métadonnées du coffre-fort si trouvé, None si le coffre-fort n'est pas initialisé
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
        "kdf_params": json.loads(kdf_params),  # Désérialise les paramètres de la DDK depuis JSON
        "salt": salt,
        "verifier": verifier,
        "version": version,
    }


def list_entries(con: sqlite3.Connection) -> list[Entry]:
    """
    Récupère toutes les entrées du coffre-fort, triées par date de modification.

    Args:
        con: Connexion à la base de données

    Returns:
        Liste de toutes les entrées, les plus récentes en premier
    """
    rows = con.execute(
        """
        SELECT id, url, title, username, password_ct, nonce
        FROM entries
        ORDER BY updated_at DESC
        """
    ).fetchall()
    return [Entry(*row) for row in rows]

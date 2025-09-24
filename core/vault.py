"""
Module principal du coffre-fort pour le gestionnaire de mots de passe.
Gère les principales opérations du coffre-fort, y compris l'initialisation, la gestion des mots de passe,
et le stockage/récupération sécurisés des entrées.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path
from typing import Optional

from core import generator
from core.generator import StrengthResult, validate_password_strength
from crypto import aead
from crypto.key_derivation import derive_key
from crypto.keyring import Keyring
from storage import repository, schema
from storage.repository import Entry


class Vault:
    """Classe principale pour la gestion du coffre-fort de mots de passe"""

    def __init__(self, db_path: Path):
        """
        Initialise une nouvelle instance du coffre-fort.

        Args:
            db_path: Chemin vers le fichier de base de données SQLite
        """
        self.con = schema.open_db(db_path)
        self._keyring = Keyring()

    def validate_master_password(self, password: str) -> StrengthResult:
        """Valide le mot de passe maître en utilisant les critères de sécurité"""
        return validate_password_strength(
            password,
            min_length=12,
            require_types=4,  # Exige tous les types : majuscules, minuscules, chiffres, spéciaux
        )

    def init_master_password(self, master_password: str):
        """
        Initialise le coffre-fort avec un mot de passe maître fort.
        Vérifie la robustesse et crée le vault_meta dans la base.

        Args:
            master_password: Le mot de passe maître à utiliser pour le chiffrement

        Raises:
            RuntimeError: Si le coffre-fort est déjà initialisé
            ValueError: Si le mot de passe maître est trop faible
        """
        # Vérifie si le coffre-fort est déjà initialisé
        meta = repository.load_vault_meta(self.con)
        if meta:
            raise RuntimeError("Vault déjà initialisée")

        # Vérification de la robustesse du mot de passe
        result = self.validate_master_password(master_password)
        if not result.ok:
            raise ValueError("Mot de passe maître trop faible : " + "; ".join(result.reasons))

        # Dérive la clé via Argon2 :
        key, params = derive_key(master_password, None)

        # Stocke le hash de la clé dans la base pour vérification future
        verifier = hashlib.sha256(key).digest()
        repository.save_vault_meta(self.con, {
            "kdf_name": "argon2id",
            "kdf_params": params.to_dict(),
            "salt": params.salt,
            "verifier": verifier,
            "version": 1,
        })

        # Débloque le coffre-fort avec le keyring
        self._keyring.unlock(master_password, params)

    def add_entry(
        self,
        url: str,
        title: Optional[str],
        username: Optional[str],
        password: str,
    ) -> int:
        """
        Ajoute une nouvelle entrée au coffre-fort.

        Args:
            url: URL du service
            title: Titre de l'entrée (optionnel, utilise l'URL par défaut)
            username: Nom d'utilisateur (optionnel)
            password: Mot de passe à stocker

        Returns:
            L'ID de la nouvelle entrée

        Raises:
            AssertionError: Si le coffre-fort est verrouillé
            ValueError: Si le mot de passe maître est trop faible
        """
        if not self._keyring.is_unlocked():
            raise AssertionError("Vault verrouillé : appelez unlock d'abord")

        key = self._keyring.get_key()
        # On convertit le mot de passe en bytes
        plaintext = password.encode("utf-8")
        # On chiffre le mot de passe
        ct, nonce = aead.encrypt(key, plaintext, aad=url.encode("utf-8"))
        entry = Entry(
            id=None,
            url=url,
            title=title or url,  # si title absent, on met l'url comme titre
            username=username,
            password_ct=ct,
            nonce=nonce,
        )
        return repository.add_entry(self.con, entry)

    def get_entry(self, entry_id: int, reveal: bool = False) -> Optional[Entry]:
        """Récupère une entrée par son ID. reveal=True pour lire le mot de passe en clair."""
        entry = repository.get_entry(self.con, entry_id)
        if entry and reveal:
            if not self._keyring.is_unlocked():
                raise AssertionError("Vault verrouillé")
            key = self._keyring.get_key()
            clear = aead.decrypt(key, entry.nonce, entry.password_ct, aad=entry.url.encode("utf-8"))
            entry.password_ct = clear.decode("utf-8")
        return entry

    def search(self, query: str) -> Iterable[Entry]:
        """Recherche des entrées par URL, titre ou nom d'utilisateur"""
        return repository.search(self.con, query)

    def delete(self, entry_id: int) -> bool:
        """Supprime une entrée par son ID"""
        return repository.delete(self.con, entry_id)

    def lock(self):
        """Verrouille le coffre-fort en effaçant le keyring."""
        self._keyring.lock()

    # ---------- Génération de mot de passe ----------
    def generate_password(
        self,
        length: int = 16,
        use_digits: bool = True,
        use_specials: bool = True,
        use_upper: bool = True,
        use_lower: bool = True,
    ) -> str:
        """Génère un mot de passe fort via core.generator."""
        return generator.generate_password(
            length=length,
            use_digits=use_digits,
            use_specials=use_specials,
            use_upper=use_upper,
            use_lower=use_lower,
        )

    def list_passwords(self) -> list[Entry]:
        """Liste toutes les entrées du coffre-fort"""
        return repository.list_entries(self.con)

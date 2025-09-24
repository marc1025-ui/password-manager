from pathlib import Path
from typing import Optional, Iterable
from storage import repository, schema
from storage.repository import Entry
from crypto.key_derivation import derive_key
from pathlib import Path
from typing import Optional, Iterable
from storage import repository, schema
from storage.repository import Entry
from core import generator
from core.generator import validate_password_strength, StrengthResult
from crypto import aead, key_derivation
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from crypto.keyring import Keyring
import hashlib


class Vault:
    """main class for managing the password vault"""

    def __init__(self, db_path: Path):
        self.con = schema.open_db(db_path)
        self._keyring = Keyring()

    def validate_master_password(self, password: str) -> StrengthResult:
        """Valide le mot de passe maître en utilisant les critères de sécurité"""
        return validate_password_strength(
            password,
            min_length=12,
            require_types=4,  # Require all types: upper, lower, digits, special
        )

    def init_master_password(self, master_password: str):
        """
        Initialise la vault avec un mot de passe maître fort.
        Vérifie la robustesse et crée le vault_meta dans la base.
        """
        # Vérifie si la vault est déjà initialisée
        meta = repository.load_vault_meta(self.con)
        if meta:
            raise RuntimeError("Vault déjà initialisée")

        # Vérification de la robustesse du mot de passe
        result = self.validate_master_password(master_password)
        if not result.ok:
            raise ValueError(
                "Mot de passe maître trop faible : " + "; ".join(result.reasons)
            )

        # Dérive la clé via Argon2 :
        key, params = derive_key(master_password, None)

        # Stocke le hash de la clé dans la base pour vérification future
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

        # Débloque la vault avec le keyring
        self._keyring.unlock(master_password, params)

    def add_entry(
        self,
        url: str,
        title: Optional[str],
        username: Optional[str],
        password: str,
        master_password: Optional[str] = None,
        auto_lock: bool = True,
    ) -> int:
        """
        Ajoute une nouvelle entrée au vault.

        Args:
            url: URL du service
            title: Titre de l'entrée (optionnel, utilise l'URL par défaut)
            username: Nom d'utilisateur (optionnel)
            password: Mot de passe à stocker
            master_password: Mot de passe maître pour déverrouiller si nécessaire
            auto_lock: Si True, reverrouille le vault après l'ajout

        Returns:
            L'ID de la nouvelle entrée
        """
        was_locked = not self._keyring.is_unlocked()

        # Si le vault est verrouillé, tenter de le déverrouiller
        if was_locked:
            if not master_password:
                raise AssertionError(
                    "Vault verrouillé : fournissez le master_password pour déverrouiller automatiquement"
                )

            try:
                self.unlock(master_password)
            except Exception as e:
                raise ValueError(f"Impossible de déverrouiller le vault : {e}")

        try:
            # Ajouter l'entrée
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

        finally:
            # Reverrouiller le vault si il était verrouillé avant et auto_lock est activé
            if was_locked and auto_lock:
                self.lock()

    def get_entry(self, entry_id: int, reveal: bool = False) -> Optional[Entry]:
        """Récupère une entrée par son ID. reveal=True pour lire le mot de passe en clair."""
        entry = repository.get_entry(self.con, entry_id)
        if entry and reveal:
            if not self._keyring.is_unlocked():
                raise AssertionError("Vault verrouillé")
            key = self._keyring.get_key()
            clear = aead.decrypt(
                key, entry.nonce, entry.password_ct, aad=entry.url.encode("utf-8")
            )
            entry.password_ct = clear.decode("utf-8")
        return entry

    def search(self, query: str) -> Iterable[Entry]:
        """search entries by url, title or username"""
        return repository.search(self.con, query)

    def delete(self, entry_id: int) -> bool:
        """delete an entry by its ID"""
        return repository.delete(self.con, entry_id)

    def lock(self):
        self._keyring.lock()

    def unlock(self, master_password: str):
        """Déverrouille le vault avec le mot de passe maître"""
        # Charger les métadonnées du vault
        meta = repository.load_vault_meta(self.con)
        if not meta:
            msg = "Vault non initialisé. Appelez init_master_password() d'abord."
            raise RuntimeError(msg)

        # Déverrouiller le keyring avec les métadonnées stockées
        self._keyring.unlock(master_password, meta)

    def is_unlocked(self) -> bool:
        return self._keyring.is_unlocked()

    def list_passwords(self) -> list[Entry]:
        """Liste toutes les entrées du vault"""
        return repository.list_entries(self.con)

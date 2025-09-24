"""
Module Keyring pour la gestion sécurisée des clés.
Gère le stockage des clés de chiffrement en mémoire avec nettoyage sécurisé
et vérification du mot de passe maître.
"""

import hashlib
from typing import Optional, Union

from crypto.key_derivation import derive_key, KDFParams


class Keyring:
    """
    Classe de stockage et de gestion de clés sécurisée.

    Gère les clés de chiffrement en mémoire avec nettoyage automatique
    et fournit une fonctionnalité de vérification du mot de passe maître.
    """

    def __init__(self):
        """Initialiser le keyring vide."""
        self._key: Optional[bytes] = None
        self._params: Optional[KDFParams] = None

    def unlock(
        self, master_password: str, vault_meta_or_params: Union[dict, KDFParams]
    ):
        """
        Déverrouiller le keyring avec vérification du mot de passe maître.

        Args:
            master_password: Le mot de passe maître à vérifier
            vault_meta_or_params: Soit un objet KDFParams, soit un dictionnaire de métadonnées de coffre-fort
                                 contenant kdf_params et verifier

        Raises:
            ValueError: Si le mot de passe maître est incorrect
        """
        # Gérer les deux formats d'appel possibles
        if isinstance(vault_meta_or_params, KDFParams):
            # Cas 1: appel direct depuis vault.py avec un objet KDFParams
            params = vault_meta_or_params
            verifier = None  # Pas de vérification dans ce cas
        else:
            # Cas 2: appel depuis l'app avec un dictionnaire vault_meta
            vault_meta = vault_meta_or_params
            kdf_params_data = vault_meta["kdf_params"]

            if isinstance(kdf_params_data, KDFParams):
                params = kdf_params_data
            else:
                # C'est un dict, on doit le convertir
                params = KDFParams.from_dict(kdf_params_data)

            verifier = vault_meta.get("verifier")

        # Deriver la clé du mot de passe maître
        key, _ = derive_key(master_password, params)

        # Vérification via le verifier seulement si on en a un
        if verifier is not None and hashlib.sha256(key).digest() != verifier:
            raise ValueError("Mot de passe maître incorrect")

        # Stocker la clé et les paramètres en mémoire
        self._key = key
        self._params = params

    def get_key(self) -> bytes:
        """
        Obtenir la clé de chiffrement actuelle.

        Returns:
            Les octets de la clé de chiffrement

        Raises:
            RuntimeError: Si le coffre-fort est verrouillé (aucune clé disponible)
        """
        if not self._key:
            raise RuntimeError("Coffre-fort verrouillé : aucune clé disponible")
        return self._key

    def lock(self):
        """
        Verrouiller le keyring et effacer en toute sécurité les clés de la mémoire.

        Effectue un nettoyage sécurisé des données en mémoire en écrasant
        les octets de clé avant la suppression.
        """
        if self._key:
            # Best effort : écraser les octets avant suppression
            mutable = bytearray(self._key)
            for i in range(len(mutable)):
                mutable[i] = 0
        self._key = None
        self._params = None

    def is_unlocked(self) -> bool:
        """
        Vérifier si le keyring est actuellement déverrouillé.

        Returns:
            True si le keyring a une clé valide, False sinon
        """
        return self._key is not None

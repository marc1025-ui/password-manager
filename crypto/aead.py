"""
Module de chiffrement authentifié avec données associées (AEAD).
Fournit un chiffrement AES-256-GCM pour le stockage sécurisé des mots de passe
avec protection par authentification et intégrité.
"""

from os import urandom
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt(key: bytes, plaintext: bytes, aad: bytes) -> tuple[bytes, bytes]:
    """Chiffre du texte en clair en utilisant AES-256-GCM avec des données associées.

    Args:
        key: 32-byte clé de chiffrement
        plaintext: Données à chiffrer
        aad: Données associées authentifiées (non chiffrées mais authentifiées)

    Returns:
        Tuple de (texte chiffré, nonce)

    Raises:
        ValueError: Si la longueur de la clé est invalide

    Examples:
        >>> key = urandom(32)
        >>> ct, nonce = encrypt(key, b"secret", b"context")
        >>> len(ct) >= len(b"secret")  # Le texte chiffré inclut la balise d'authentification
        True
        >>> len(nonce)
        12
    """
    # Générer un nonce aléatoire pour ce chiffrement
    nonce = urandom(12)  # 96-bit nonce pour GCM

    # Créer une instance du cipher AESGCM
    aesgcm = AESGCM(key)

    # Chiffrer et authentifier
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

    return ciphertext, nonce


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
    """Déchiffre du texte chiffré en utilisant AES-256-GCM et vérifie l'authenticité.

    Args:
        key: 32-byte clé de déchiffrement (doit correspondre à la clé de chiffrement)
        nonce: Nonce utilisé lors du chiffrement
        ciphertext: Données chiffrées avec balise d'authentification
        aad: Données associées authentifiées (doivent correspondre aux AAD de chiffrement)

    Returns:
        Octets du texte en clair déchiffré

    Raises:
        cryptography.exceptions.InvalidTag: Si l'authentification échoue
        ValueError: Si la longueur de la clé/nonce est invalide

    Examples:
        >>> key = urandom(32)
        >>> ct, nonce = encrypt(key, b"secret", b"context")
        >>> decrypt(key, nonce, ct, b"context")
        b'secret'
    """
    # Créer une instance du cipher AESGCM
    aesgcm = AESGCM(key)

    # Déchiffrer et vérifier l'authenticité
    return aesgcm.decrypt(nonce, ciphertext, aad)

"""
Authenticated Encryption with Associated Data (AEAD) module.
Provides AES-256-GCM encryption for secure password storage
with authentication and integrity protection.
"""

from os import urandom

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt(key: bytes, plaintext: bytes, aad: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext using AES-256-GCM with associated data.

    Args:
        key: 32-byte encryption key
        plaintext: Data to encrypt
        aad: Associated authenticated data (not encrypted but authenticated)

    Returns:
        Tuple of (ciphertext, nonce)

    Raises:
        ValueError: If key length is invalid

    Examples:
        >>> key = urandom(32)
        >>> ct, nonce = encrypt(key, b"secret", b"context")
        >>> len(ct) >= len(b"secret")  # Ciphertext includes auth tag
        True
        >>> len(nonce)
        12
    """
    # Generate random nonce for this encryption
    nonce = urandom(12)  # 96-bit nonce for GCM

    # Create AESGCM cipher instance
    aesgcm = AESGCM(key)

    # Encrypt and authenticate
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

    return ciphertext, nonce


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
    """
    Decrypt ciphertext using AES-256-GCM and verify authenticity.

    Args:
        key: 32-byte decryption key (must match encryption key)
        nonce: Nonce used during encryption
        ciphertext: Encrypted data with authentication tag
        aad: Associated authenticated data (must match encryption AAD)

    Returns:
        Decrypted plaintext bytes

    Raises:
        cryptography.exceptions.InvalidTag: If authentication fails
        ValueError: If key/nonce length is invalid

    Examples:
        >>> key = urandom(32)
        >>> ct, nonce = encrypt(key, b"secret", b"context")
        >>> decrypt(key, nonce, ct, b"context")
        b'secret'
    """
    # Create AESGCM cipher instance
    aesgcm = AESGCM(key)

    # Decrypt and verify authenticity
    return aesgcm.decrypt(nonce, ciphertext, aad)


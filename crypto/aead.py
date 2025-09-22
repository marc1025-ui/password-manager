from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from os import urandom

NONCE_LEN = 12


def encrypt(key: bytes, plaintext: bytes, aad: bytes) -> tuple[bytes, bytes]:
    aesgcm = AESGCM(key)
    nonce = urandom(NONCE_LEN)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return ct, nonce


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes ) -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, aad)

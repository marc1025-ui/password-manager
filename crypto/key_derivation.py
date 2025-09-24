"""
Key derivation functions and parameters for the password manager.
Implements Argon2id key derivation with configurable parameters
for secure master password processing.
"""

from __future__ import annotations

from dataclasses import dataclass
from os import urandom

from argon2.low_level import Type, hash_secret_raw


@dataclass
class KDFParams:
    """
    Key Derivation Function parameters for Argon2.

    Attributes:
        time_cost: Number of iterations (computational cost)
        memory_cost: Memory usage in KiB
        parallelism: Number of parallel threads
        salt: Random salt bytes for key derivation
        hash_len: Length of derived key in bytes
    """

    time_cost: int = 2
    memory_cost: int = 256 * 1024  # KiB
    parallelism: int = 4
    salt: bytes = b""
    hash_len: int = 32

    def to_dict(self) -> dict:
        """
        Convert KDFParams to dictionary for serialization.

        Returns:
            Dictionary representation with salt as hex string
        """
        return {
            "time_cost": self.time_cost,
            "memory_cost": self.memory_cost,
            "parallelism": self.parallelism,
            "salt": self.salt.hex() if isinstance(self.salt, bytes) else self.salt,
            "hash_len": self.hash_len,
        }

    @staticmethod
    def from_dict(data) -> KDFParams:
        """
        Create KDFParams from dictionary data.

        Args:
            data: Dictionary with KDF parameters or existing KDFParams object

        Returns:
            KDFParams instance
        """
        # Si data est déjà un objet KDFParams, le retourner directement
        if isinstance(data, KDFParams):
            return data

        # Sinon, c'est un dict, on le traite normalement
        params_dict = data.copy()
        if isinstance(params_dict.get("salt"), str):
            params_dict["salt"] = bytes.fromhex(params_dict["salt"])
        return KDFParams(**params_dict)


def derive_key(password: str, params: KDFParams) -> tuple[bytes, KDFParams]:
    """
    Derive a cryptographic key from password using Argon2id.

    Args:
        password: The password to derive key from
        params: KDF parameters (if None, generates new params with random salt)

    Returns:
        Tuple of (derived_key, kdf_params_used)

    Examples:
        >>> key, params = derive_key("my_password", None)
        >>> len(key)
        32
        >>> len(params.salt)
        16
    """
    if params is None:
        params = KDFParams(salt=urandom(16))

    # Derive key using Argon2id
    key = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=params.salt,
        time_cost=params.time_cost,
        memory_cost=params.memory_cost,
        parallelism=params.parallelism,
        hash_len=params.hash_len,
        type=Type.ID,  # Argon2id variant
    )
    return key, params

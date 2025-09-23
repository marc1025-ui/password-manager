from dataclasses import dataclass
from os import urandom
from typing import Dict

from argon2.low_level import Type, hash_secret_raw


@dataclass
class KDFParams:
    time_cost: int = 2
    memory_cost: int = 256 * 1024  # KiB
    parallelism: int = 4
    salt: bytes = b""
    hash_len: int = 32

    def to_dict(self) -> Dict:
        return {
            "time_cost": self.time_cost,
            "memory_cost": self.memory_cost,
            "parallelism": self.parallelism,
            "salt": self.salt.hex() if isinstance(self.salt, bytes) else self.salt,
            "hash_len": self.hash_len,
        }

    @staticmethod
    def from_dict(data) -> 'KDFParams':
        # Si data est déjà un objet KDFParams, le retourner directement
        if isinstance(data, KDFParams):
            return data

        # Sinon, c'est un dict, on le traite normalement
        params_dict = data.copy()
        if isinstance(params_dict.get('salt'), str):
            params_dict['salt'] = bytes.fromhex(params_dict['salt'])
        return KDFParams(**params_dict)


def derive_key(password: str, params: KDFParams ) -> tuple[bytes, KDFParams]:
    if params is None:
        params = KDFParams(salt=urandom(16))
    key = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=params.salt,
        time_cost=params.time_cost,
        memory_cost=params.memory_cost,
        parallelism=params.parallelism,
        hash_len=params.hash_len,
        type=Type.ID,
    )
    return key, params
from typing import Optional
from crypto.key_derivation import derive_key, KDFParams

class Keyring:
    def __init__(self):
        self._key: Optional[bytes] = None
        self._params: Optional[KDFParams] = None

    def unlock(self, master_password: str, params: KDFParams) -> bool:
        key, _ = derive_key(master_password, params)
        self._key = key
        self._params = params
        return True

    def get_key(self) -> bytes:
        if not self._key:
            raise RuntimeError("Vault verrouillé : clé absente")
        return self._key

    def lock(self):
        if self._key:
            # Best effort : écraser les octets avant suppression
            mutable = bytearray(self._key)
            for i in range(len(mutable)):
                mutable[i] = 0
        self._key = None
        self._params = None

    def is_unlocked(self) -> bool:
        return self._key is not None

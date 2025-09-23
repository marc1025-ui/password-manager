import hashlib
from typing import Optional, Union
from crypto.key_derivation import derive_key, KDFParams

class Keyring:
    def __init__(self):
        self._key: Optional[bytes] = None
        self._params: Optional[KDFParams] = None
        
    def unlock(self, master_password: str, vault_meta_or_params: Union[dict, KDFParams]):
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

        key, _ = derive_key(master_password, params)
        
        # Vérification via le verifier seulement si on en a un
        if verifier is not None:
            if hashlib.sha256(key).digest() != verifier:
                raise ValueError("Mot de passe maître incorrect")

        self._key = key
        self._params = params

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

from pathlib import Path
from typing import Optional, Iterable
from storage import repository, schema
from storage.repository import Entry
from core import generator


from pathlib import Path
from typing import Optional, Iterable
from storage import repository, schema
from storage.repository import Entry
from core import generator


class Vault:
    """main class for managing the password vault"""
    def __init__(self, db_path: Path):
        self.con = schema.open_db(db_path)

    # ---------- Entrées ----------
    def add_entry(
        self,
        url: str,
        title: Optional[str],
        username: Optional[str],
        password: str,
    ) -> int:
        """add a new entry to the vault, returns the new entry ID"""
        # TODO : plus tard, chiffrer `password` avec crypto
        entry = Entry(
            id=None,
            url=url,
            title=title or url,  # si title absent, on met l'url comme titre
            username=username,
            password_ct=password.encode("utf-8"),
            nonce=b"",  # provisoire pour futur chiffrement
        )
        return repository.add_entry(self.con, entry)

    def get_entry(self, entry_id: int, reveal: bool = False) -> Optional[Entry]:
        """Récupère une entrée par son ID. reveal=True pour lire le mot de passe en clair."""
        entry = repository.get_entry(self.con, entry_id)
        if entry and reveal:
            # TODO : déchiffrement futur
            entry.password_ct = entry.password_ct.decode("utf-8")
        return entry

    def search(self, query: str) -> Iterable[Entry]:
        """search entries by url, title or username"""
        return repository.search(self.con, query)

    def delete(self, entry_id: int) -> bool:
        """delete an entry by its ID"""
        return repository.delete(self.con, entry_id)

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
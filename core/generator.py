# core/generator.py
import secrets
import string
import re
from typing import NamedTuple


class StrengthResult(NamedTuple):
    """Résultat de la vérification de robustesse d'un mot de passe."""
    ok: bool
    reasons: list[str]


def generate_password(
    length: int = 16,
    use_digits: bool = True,
    use_specials: bool = True,
    use_upper: bool = True,
    use_lower: bool = True,
) -> str:
    alphabet = ""
    if use_lower:
        alphabet += string.ascii_lowercase
    if use_upper:
        alphabet += string.ascii_uppercase
    if use_digits:
        alphabet += string.digits
    if use_specials:
        alphabet += "!@#$%^&*()-_=+[]{};:,.<>?/"

    if not alphabet:
        raise ValueError("Alphabet vide : impossible de générer un mot de passe.")

    return "".join(secrets.choice(alphabet) for _ in range(length))


def validate_password_strength(
    password: str,
    min_length: int = 12,
    require_types: int = 3
) -> StrengthResult:
    """
    Vérifie la robustesse d'un mot de passe.
    - min_length : longueur minimale
    - require_types : nombre de types de caractères différents requis
      (majuscule, minuscule, chiffre, spécial)
    """
    reasons: list[str] = []

    if len(password) < min_length:
        reasons.append(f"Password too short (< {min_length}).")

    types_present = 0
    if re.search(r"[a-z]", password):
        types_present += 1
    if re.search(r"[A-Z]", password):
        types_present += 1
    if re.search(r"\d", password):
        types_present += 1
    if re.search(r"[!@#$%^&*()\-\_=+\[\]{};:,.<>?/]", password):
        types_present += 1

    if types_present < require_types:
        reasons.append(
            f"Le mot de passe doit contenir au moins {require_types} types de caractères "
            "(maj, min, chiffres, spéciaux)."
        )

    return StrengthResult(ok=(len(reasons) == 0), reasons=reasons)
"""
Module de génération de mots de passe et de validation de la force.
Fournit une génération de mots de passe sécurisée avec des paramètres personnalisables
et une validation complète de la force du mot de passe.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import List


@dataclass
class StrengthResult:
    """Résultat de validation de la force du mot de passe"""

    ok: bool
    reasons: List[str]


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_specials: bool = True,
) -> str:
    """Génère un mot de passe aléatoire cryptographiquement sécurisé.

    Args:
        length: Longueur du mot de passe (par défaut : 16)
        use_upper: Inclure des lettres majuscules A-Z
        use_lower: Inclure des lettres minuscules a-z
        use_digits: Inclure des chiffres 0-9
        use_specials: Inclure des caractères spéciaux !@#$%^&*()_+-=[]{}|;:,.<>?

    Returns:
        Chaîne de caractères du mot de passe généré aléatoirement

    Raises:
        ValueError: Si aucun type de caractère n'est sélectionné

    Examples:
        >>> generate_password(12, use_specials=False)
        'Kj8mN2pQ9rL4'
        >>> generate_password(8, use_upper=False, use_lower=True, use_digits=True)
        'k8j2m9p4'
    """
    # Ensembles de caractères
    charset = ""
    if use_upper:
        charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if use_lower:
        charset += "abcdefghijklmnopqrstuvwxyz"
    if use_digits:
        charset += "0123456789"
    if use_specials:
        charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Valider qu'au moins un type de caractère est sélectionné
    if not charset:
        raise ValueError("Au moins un type de caractère doit être sélectionné")

    # Générer le mot de passe en utilisant un choix aléatoire cryptographiquement sécurisé
    return "".join(secrets.choice(charset) for _ in range(length))


def validate_password_strength(
    password: str, min_length: int = 8, require_types: int = 3
) -> StrengthResult:
    """Valide la force du mot de passe selon des critères de sécurité.

    Args:
        password: Mot de passe à valider
        min_length: Longueur minimale requise
        require_types: Nombre de types de caractères requis (1-4)
                      1: Tous les caractères
                      2: Mélange de 2 types (par ex., lettres + chiffres)
                      3: Mélange de 3 types (par ex., maj + min + chiffres)
                      4: Tous les types (maj + min + chiffres + spéciaux)

    Returns:
        StrengthResult avec le résultat de la validation et les raisons d'échec

    Examples:
        >>> result = validate_password_strength("Password123!")
        >>> result.ok
        True
        >>> result = validate_password_strength("weak")
        >>> result.ok
        False
        >>> "too short" in " ".join(result.reasons)
        True
    """
    reasons = []

    # Vérifier la longueur minimale
    if len(password) < min_length:
        reasons.append(f"Le mot de passe doit contenir au moins {min_length} caractères")

    # Vérifier si le mot de passe est vide
    if not password:
        reasons.append("Le mot de passe ne peut pas être vide")
        return StrengthResult(ok=False, reasons=reasons)

    # Détection des types de caractères
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"[0-9]", password))
    has_special = bool(re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password))

    # Compter les types de caractères présents
    types_present = sum([has_upper, has_lower, has_digit, has_special])

    # Vérifier les exigences de types de caractères
    if types_present < require_types:
        reasons.append(
            f"Le mot de passe doit contenir au moins {require_types} types de caractères "
            "(maj, min, chiffres, spéciaux)."
        )

    # Vérifier les motifs faibles courants
    if password.lower() in [
        "password",
        "123456",
        "qwerty",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
    ]:
        reasons.append("Le mot de passe est trop commun et facilement devinable")

    # Vérifier les motifs simples
    if re.match(r"^(.)\1+$", password):  # Tout le même caractère
        reasons.append("Le mot de passe ne peut pas être composé du même caractère")

    if re.match(r"^(012|123|234|345|456|567|678|789|890)+", password):
        reasons.append("Le mot de passe contient des séquences numériques prévisibles")

    if re.match(r"^(abc|def|ghi|jkl|mno|pqr|stu|vwx)+", password.lower()):
        reasons.append("Le mot de passe contient des séquences de lettres prévisibles")

    # Vérifications supplémentaires pour les mots de passe très courts
    if len(password) < 6:
        reasons.append("Le mot de passe est critique court (moins de 6 caractères)")

    # Vérifier les motifs de clavier (de base)
    keyboard_patterns = ["qwerty", "asdf", "zxcv", "1234", "abcd"]
    password_lower = password.lower()
    for pattern in keyboard_patterns:
        if pattern in password_lower:
            reasons.append("Le mot de passe contient des motifs de clavier")
            break

    return StrengthResult(ok=len(reasons) == 0, reasons=reasons)

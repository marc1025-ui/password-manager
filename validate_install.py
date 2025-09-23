#!/usr/bin/env python3
"""
Script de validation de l'installation.
Vérifie que tous les composants sont correctement installés.
"""

import sys
import importlib
import subprocess
from pathlib import Path


def test_imports():
    """Test que tous les modules peuvent être importés"""
    modules_to_test = [
        'core.vault',
        'core.generator',
        'crypto.keyring',
        'crypto.key_derivation',
        'crypto.aead',
        'storage.repository',
        'storage.schema',
        'ui.app_qt',
    ]

    print("🔍 Test des imports...")

    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            return False

    return True


def test_dependencies():
    """Test que toutes les dépendances sont installées"""
    dependencies = [
        'cryptography',
        'argon2',
        'PySide6',
    ]

    print("\n📦 Test des dépendances...")

    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"  ✅ {dep}")
        except Exception as e:
            print(f"  ❌ {dep}: {e}")
            return False

    return True


def test_entry_points():
    """Test que les points d'entrée sont correctement installés"""
    print("\n🚀 Test des commandes installées...")

    commands = [
        ('password-manager-gui', 'ui.app_qt:main'),
        ('password-manager', 'ui.cli:main'),
        ('pwmgr', 'ui.cli:main'),
    ]

    for cmd, module in commands:
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ {cmd} -> {result.stdout.strip()}")
            else:
                print(f"  ⚠️  {cmd} non trouvé dans PATH")
        except Exception as e:
            print(f"  ❌ Erreur test {cmd}: {e}")


def test_functionality():
    """Test rapide des fonctionnalités principales"""
    print("\n🧪 Test des fonctionnalités...")

    try:
        # Test génération de mot de passe
        from core.generator import generate_password
        password = generate_password(length=12)
        assert len(password) == 12
        print("  ✅ Génération de mots de passe")

        # Test dérivation de clés
        from crypto.key_derivation import KDFParams, derive_key
        import os
        params = KDFParams(salt=os.urandom(16))
        key, _ = derive_key("test", params)
        assert len(key) == 32
        print("  ✅ Dérivation de clés")

        # Test chiffrement
        from crypto import aead
        key = os.urandom(32)
        plaintext = b"test message"
        ct, nonce = aead.encrypt(key, plaintext, b"aad")
        decrypted = aead.decrypt(key, nonce, ct, b"aad")
        assert decrypted == plaintext
        print("  ✅ Chiffrement/déchiffrement")

        # Test vault temporaire
        import tempfile
        from core.vault import Vault

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            vault_path = Path(f.name)

        try:
            vault = Vault(vault_path)
            # Test basique sans initialisation complète
            print("  ✅ Création de vault")
        finally:
            vault_path.unlink(missing_ok=True)

        return True

    except Exception as e:
        print(f"  ❌ Erreur fonctionnalité: {e}")
        return False


def main():
    """Fonction principale de validation"""
    print("🔐 Validation de l'installation du Password Manager")
    print("=" * 55)

    all_tests_passed = True

    # Tests individuels
    tests = [
        ("Imports", test_imports),
        ("Dépendances", test_dependencies),
        ("Fonctionnalités", test_functionality),
    ]

    for test_name, test_func in tests:
        success = test_func()
        if not success:
            all_tests_passed = False

    # Test des points d'entrée (informatif seulement)
    test_entry_points()

    # Résumé final
    print("\n" + "=" * 55)
    if all_tests_passed:
        print("🎉 ✅ Installation validée avec succès !")
        print("\n📱 Votre application est prête à être utilisée :")
        print("   Interface graphique: password-manager-gui")
        print("   Ligne de commande:   password-manager")
        print("   Direct Python:       python -m ui.app_qt")
        print("\n🧪 Tests complets:       python run_tests.py")
    else:
        print("❌ ⚠️  Problèmes détectés dans l'installation")
        print("Réinstallez avec: pip install -e .")
        sys.exit(1)


if __name__ == "__main__":
    main()

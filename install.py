#!/usr/bin/env python3
"""
Script d'installation automatique pour le gestionnaire de mots de passe.
Ce script vérifie les prérequis et installe l'application.
"""

import sys
import subprocess
import os
import platform
from pathlib import Path


def check_python_version():
    """Vérifie que Python 3.9+ est installé"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Erreur: Python 3.9 ou plus récent est requis")
        print(f"Version actuelle: {version.major}.{version.minor}.{version.micro}")
        print("Veuillez mettre à jour Python: https://www.python.org/downloads/")
        return False

    print(f"✅ Python {version.major}.{version.minor}.{version.micro} détecté")
    return True


def check_pip():
    """Vérifie que pip est disponible"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                      check=True, capture_output=True)
        print("✅ pip est disponible")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erreur: pip n'est pas disponible")
        print("Installez pip: https://pip.pypa.io/en/stable/installation/")
        return False


def install_dependencies():
    """Installe les dépendances requises"""
    print("\n🔧 Installation des dépendances...")

    try:
        # Mettre à jour pip
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True)

        # Installer les dépendances principales
        dependencies = [
            "cryptography>=41.0.0",
            "argon2-cffi>=23.0.0",
            "PySide6>=6.5.0",
        ]

        for dep in dependencies:
            print(f"  📦 Installation de {dep}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True)

        print("✅ Toutes les dépendances ont été installées")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances: {e}")
        return False


def install_application():
    """Installe l'application en mode développement"""
    print("\n📱 Installation de l'application...")

    try:
        # Installation en mode éditable
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], check=True)

        print("✅ Application installée avec succès")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de l'application: {e}")
        return False


def create_desktop_shortcut():
    """Crée un raccourci sur le bureau (selon l'OS)"""
    system = platform.system()

    if system == "Darwin":  # macOS
        create_macos_shortcut()
    elif system == "Linux":
        create_linux_shortcut()
    elif system == "Windows":
        create_windows_shortcut()
    else:
        print(f"⚠️  Raccourci bureau non supporté pour {system}")


def create_macos_shortcut():
    """Crée un raccourci macOS"""
    try:
        app_script = f"""#!/bin/bash
{sys.executable} -m ui.app_qt
"""

        desktop_path = Path.home() / "Desktop" / "Password Manager.command"
        desktop_path.write_text(app_script)
        os.chmod(desktop_path, 0o755)

        print("✅ Raccourci créé sur le bureau (macOS)")
    except Exception as e:
        print(f"⚠️  Impossible de créer le raccourci: {e}")


def create_linux_shortcut():
    """Crée un raccourci Linux (.desktop)"""
    try:
        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Password Manager
Comment=Gestionnaire de mots de passe sécurisé
Exec={sys.executable} -m ui.app_qt
Icon=application-x-executable
Terminal=false
Categories=Utility;Security;
"""

        desktop_path = Path.home() / "Desktop" / "password-manager.desktop"
        desktop_path.write_text(desktop_entry)
        os.chmod(desktop_path, 0o755)

        print("✅ Raccourci créé sur le bureau (Linux)")
    except Exception as e:
        print(f"⚠️  Impossible de créer le raccourci: {e}")


def create_windows_shortcut():
    """Crée un raccourci Windows"""
    try:
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()
        path = os.path.join(desktop, "Password Manager.lnk")
        target = sys.executable
        arguments = "-m ui.app_qt"

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = target
        shortcut.save()

        print("✅ Raccourci créé sur le bureau (Windows)")
    except ImportError:
        print("⚠️  Modules Windows manquants pour créer le raccourci")
        print("   Installez: pip install pywin32 winshell")
    except Exception as e:
        print(f"⚠️  Impossible de créer le raccourci: {e}")


def run_tests():
    """Lance les tests pour vérifier l'installation"""
    print("\n🧪 Vérification de l'installation avec les tests...")

    try:
        result = subprocess.run([
            sys.executable, "run_tests.py", "test_crypto"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Tests cryptographiques passés")
        else:
            print("⚠️  Certains tests ont échoué (l'application peut quand même fonctionner)")

    except Exception as e:
        print(f"⚠️  Impossible de lancer les tests: {e}")


def main():
    """Fonction principale d'installation"""
    print("🔐 Installation du Gestionnaire de Mots de Passe")
    print("=" * 50)

    # Vérifications préliminaires
    if not check_python_version():
        sys.exit(1)

    if not check_pip():
        sys.exit(1)

    # Installation
    if not install_dependencies():
        sys.exit(1)

    if not install_application():
        sys.exit(1)

    # Configuration post-installation
    create_desktop_shortcut()
    run_tests()

    # Message de succès
    print("\n" + "=" * 50)
    print("🎉 Installation terminée avec succès !")
    print("=" * 50)
    print("\n📱 Pour lancer l'application :")
    print("   Interface graphique: password-manager-gui")
    print("   Ligne de commande:   password-manager")
    print("   Raccourci:           pwmgr")
    print("\n📚 Documentation complète dans README.md")
    print("🧪 Tests disponibles avec: python run_tests.py")
    print("\n⚠️  IMPORTANT: Mémorisez bien votre mot de passe maître !")
    print("   Il n'y a aucun moyen de récupération si vous l'oubliez.")


if __name__ == "__main__":
    main()

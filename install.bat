@echo off
REM Script d'installation pour Windows
REM Installation automatique du gestionnaire de mots de passe

echo 🔐 Installation du Gestionnaire de Mots de Passe (Windows)
echo ===========================================================

REM Vérification de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur: Python n'est pas installé ou pas dans le PATH
    echo Téléchargez Python depuis: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python détecté

REM Vérification de pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur: pip n'est pas disponible
    pause
    exit /b 1
)

echo ✅ pip disponible

REM Mise à jour de pip
echo 🔧 Mise à jour de pip...
python -m pip install --upgrade pip

REM Installation des dépendances
echo 📦 Installation des dépendances...
python -m pip install cryptography>=41.0.0
python -m pip install argon2-cffi>=23.0.0
python -m pip install PySide6>=6.5.0

REM Installation de l'application
echo 📱 Installation de l'application...
python -m pip install -e .

REM Création du raccourci (optionnel)
echo 🖥️  Tentative de création d'un raccourci...
python -c "
import os, sys
from pathlib import Path
try:
    import winshell
    from win32com.client import Dispatch
    desktop = winshell.desktop()
    path = os.path.join(desktop, 'Password Manager.lnk')
    target = sys.executable
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.Arguments = '-m ui.app_qt'
    shortcut.WorkingDirectory = os.getcwd()
    shortcut.save()
    print('✅ Raccourci créé sur le bureau')
except:
    print('⚠️ Raccourci non créé (modules manquants)')
"

echo.
echo 🎉 Installation terminée !
echo =========================
echo.
echo 📱 Pour lancer l'application:
echo    Interface graphique: password-manager-gui
echo    Ligne de commande:   password-manager
echo.
echo 🧪 Pour tester: python run_tests.py
echo 📚 Documentation: README.md
echo.
pause

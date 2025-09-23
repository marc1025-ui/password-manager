#!/bin/bash
# Script de création d'exécutables pour le gestionnaire de mots de passe

set -e

echo "🔐 Création d'exécutables du Password Manager"
echo "============================================="

# Vérification de PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "📦 Installation de PyInstaller..."
    pip install pyinstaller
fi

# Nettoyage
echo "🧹 Nettoyage..."
rm -rf build/ dist/ *.spec

# Variables
APP_NAME="PasswordManager"
VERSION="1.0.0"
ICON_PATH=""  # Vous pouvez ajouter un chemin d'icône ici

# Détection de l'OS
OS=$(uname -s)
echo "🖥️  Système détecté: $OS"

# Construction de l'exécutable GUI
echo "🎨 Construction de l'interface graphique..."
if [ "$OS" = "Darwin" ]; then
    # macOS - Créer une app bundle
    pyinstaller --name="$APP_NAME" \
                --onefile \
                --windowed \
                --add-data "core:core" \
                --add-data "crypto:crypto" \
                --add-data "storage:storage" \
                --add-data "ui:ui" \
                --hidden-import=ui.app_qt \
                --hidden-import=core.vault \
                --hidden-import=crypto.keyring \
                --hidden-import=storage.repository \
                ui/app_qt.py

    echo "✅ App macOS créée: dist/$APP_NAME.app"

elif [ "$OS" = "Linux" ]; then
    # Linux
    pyinstaller --name="$APP_NAME" \
                --onefile \
                --windowed \
                --add-data "core:core" \
                --add-data "crypto:crypto" \
                --add-data "storage:storage" \
                --add-data "ui:ui" \
                --hidden-import=ui.app_qt \
                --hidden-import=core.vault \
                --hidden-import=crypto.keyring \
                --hidden-import=storage.repository \
                ui/app_qt.py

    echo "✅ Exécutable Linux créé: dist/$APP_NAME"

else
    # Autres systèmes (Windows avec WSL, etc.)
    pyinstaller --name="$APP_NAME" \
                --onefile \
                --noconsole \
                --add-data "core;core" \
                --add-data "crypto;crypto" \
                --add-data "storage;storage" \
                --add-data "ui;ui" \
                --hidden-import=ui.app_qt \
                --hidden-import=core.vault \
                --hidden-import=crypto.keyring \
                --hidden-import=storage.repository \
                ui/app_qt.py

    echo "✅ Exécutable créé: dist/$APP_NAME.exe"
fi

# Construction de l'exécutable CLI
echo "⌨️  Construction de l'interface CLI..."
pyinstaller --name="pwmgr" \
            --onefile \
            --add-data "core:core" \
            --add-data "crypto:crypto" \
            --add-data "storage:storage" \
            --add-data "ui:ui" \
            --hidden-import=ui.cli \
            --hidden-import=core.vault \
            --hidden-import=crypto.keyring \
            --hidden-import=storage.repository \
            ui/cli.py

echo "✅ CLI créé: dist/pwmgr"

# Test des exécutables
echo "🧪 Test des exécutables..."
if [ -f "dist/$APP_NAME" ]; then
    echo "  Taille GUI: $(du -h "dist/$APP_NAME" | cut -f1)"
fi

if [ -f "dist/pwmgr" ]; then
    echo "  Taille CLI: $(du -h "dist/pwmgr" | cut -f1)"
fi

# Instructions finales
echo ""
echo "🎉 Exécutables créés avec succès !"
echo "📁 Fichiers dans dist/:"
ls -la dist/

echo ""
echo "📱 Pour distribuer:"
echo "   1. Testez les exécutables localement"
echo "   2. Créez une release GitHub avec les binaires"
echo "   3. Ou distribuez directement les fichiers"

echo ""
echo "🚀 Pour tester:"
if [ "$OS" = "Darwin" ]; then
    echo "   GUI: open dist/$APP_NAME.app"
else
    echo "   GUI: ./dist/$APP_NAME"
fi
echo "   CLI: ./dist/pwmgr --help"

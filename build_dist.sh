#!/bin/bash
# Script de création de distribution pour le gestionnaire de mots de passe

set -e

echo "🔐 Création de la distribution du Password Manager"
echo "=================================================="

# Nettoyage des anciens builds
echo "🧹 Nettoyage des anciens builds..."
rm -rf build/ dist/ *.egg-info/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Vérification des outils requis
echo "🔧 Vérification des outils..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trouvé"
    exit 1
fi

if ! python3 -c "import build" 2>/dev/null; then
    echo "📦 Installation de build..."
    pip install build
fi

if ! python3 -c "import twine" 2>/dev/null; then
    echo "📦 Installation de twine..."
    pip install twine
fi

# Lancer les tests avant la distribution
echo "🧪 Lancement des tests..."
python3 run_tests.py
if [ $? -ne 0 ]; then
    echo "❌ Les tests ont échoué. Arrêt de la distribution."
    exit 1
fi

# Vérification de la qualité du code
echo "🔍 Vérification de la qualité du code..."
if command -v ruff &> /dev/null; then
    ruff check . || echo "⚠️  Avertissements de style détectés"
fi

if command -v black &> /dev/null; then
    black --check . || echo "⚠️  Code pas entièrement formaté"
fi

# Construction du package
echo "📦 Construction du package..."
python3 -m build

# Vérification du package
echo "✅ Vérification du package..."
twine check dist/*

# Affichage des résultats
echo ""
echo "🎉 Distribution créée avec succès !"
echo "📁 Fichiers créés dans dist/:"
ls -la dist/

echo ""
echo "🚀 Pour publier:"
echo "   Test PyPI: twine upload --repository testpypi dist/*"
echo "   PyPI:      twine upload dist/*"

echo ""
echo "💻 Pour créer un exécutable:"
echo "   ./build_executable.sh"

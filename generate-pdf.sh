#!/bin/bash
# Script de génération du PDF pour le guide utilisateur

echo "🔄 Génération du PDF du guide utilisateur..."

# Méthode 1: Installer Pandoc si possible
if command -v brew &> /dev/null; then
    echo "📦 Installation de Pandoc via Homebrew..."
    brew install pandoc
    pandoc docs/user-guide/guide-utilisateur.md -o docs/user-guide/guide-utilisateur.pdf
    echo "✅ PDF généré avec Pandoc"
else
    echo "⚠️  Pandoc non disponible. Alternatives :"
    echo ""
    echo "🌐 Option 1 - En ligne (recommandé) :"
    echo "   1. Allez sur https://md-to-pdf.fly.dev/"
    echo "   2. Copiez le contenu de docs/user-guide/guide-utilisateur.md"
    echo "   3. Collez et téléchargez le PDF"
    echo ""
    echo "🖥️  Option 2 - VS Code :"
    echo "   1. Installez l'extension 'Markdown PDF'"
    echo "   2. Ouvrez guide-utilisateur.md dans VS Code"
    echo "   3. Cmd+Shift+P → 'Markdown PDF: Export'"
    echo ""
    echo "📝 Option 3 - Pages/Word :"
    echo "   1. Ouvrez guide-utilisateur.md dans un éditeur de texte"
    echo "   2. Copiez tout le contenu"
    echo "   3. Collez dans Pages/Word et exportez en PDF"
fi

echo ""
echo "📁 Livrables disponibles dans:"
echo "   docs/technical/configuration.md"
echo "   docs/user-guide/guide-utilisateur.md"
echo "   docs/tests/rapport-tests.md"
echo "   docs/deliverables/cahier-recette.md"
echo "   docs/deliverables/index-livrables.md"

# 🔐 Password Manager

[![Tests](https://github.com/marie-angekuitche/password-manager/actions/workflows/tests.yml/badge.svg)](https://github.com/marie-angekuitche/password-manager/actions/workflows/tests.yml)
[![CI](https://github.com/marie-angekuitche/password-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/marie-angekuitche/password-manager/actions/workflows/ci.yml)
[![Security](https://img.shields.io/badge/security-bandit-green)](https://github.com/marie-angekuitche/password-manager/actions)
[![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/marie-angekuitche/password-manager)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Un gestionnaire de mots de passe sécurisé avec interface graphique moderne, développé en Python avec chiffrement de niveau militaire.

## ✨ Fonctionnalités

- **🔒 Sécurité maximale** : Chiffrement AES-256-GCM avec dérivation de clés Argon2
- **🎨 Interface moderne** : Interface graphique élégante avec thème sombre
- **🔑 Génération de mots de passe** : Générateur de mots de passe forts personnalisables
- **🔍 Recherche rapide** : Recherche instantanée dans vos mots de passe
- **💾 Stockage local** : Vos données restent sur votre machine (base SQLite chiffrée)
- **⏱️ Verrouillage automatique** : Sécurité renforcée avec verrouillage temporisé
- **🚀 Installation simple** : Package Python installable avec pip

## 🛠️ Installation

### Installation depuis PyPI (recommandée)
```bash
pip install password-manager
```

### Installation depuis les sources
```bash
git clone https://github.com/marie-angekuitche/password-manager.git
cd password-manager
pip install -e .
```

### Installation pour développement
```bash
git clone https://github.com/marie-angekuitche/password-manager.git
cd password-manager
pip install -e ".[dev]"
```

## 🚀 Utilisation

### Interface graphique
```bash
# Lancer l'interface graphique
password-manager-gui

# Ou directement
python -m ui.app_qt
```

### Interface en ligne de commande
```bash
# Commandes principales
password-manager --help
pwmgr --help

# Exemples d'utilisation CLI
python -m ui.cli
```

## 📋 Prérequis

- Python 3.9 ou plus récent
- PySide6 (pour l'interface graphique)
- cryptography (pour le chiffrement)
- argon2-cffi (pour la dérivation de clés)

## 🔧 Développement

### Configuration de l'environnement
```bash
# Cloner le projet
git clone https://github.com/marie-angekuitche/password-manager.git
cd password-manager

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances de développement
pip install -e ".[dev]"
```

### Tests
```bash
# Lancer tous les tests
python run_tests.py

# Tests avec couverture
python run_tests.py --coverage

# Tests spécifiques
python run_tests.py test_crypto
python run_tests.py test_vault
python run_tests.py test_generator
```

### Outils de qualité de code
```bash
# Formatage du code
black .

# Vérification du style
ruff check .

# Vérification des types
mypy .

# Tests de sécurité
bandit -r core crypto storage ui
```

## 🏗️ Architecture

```
password-manager/
├── core/           # Logique métier principale
│   ├── vault.py    # Gestion du coffre-fort
│   └── generator.py # Génération de mots de passe
├── crypto/         # Modules cryptographiques
│   ├── aead.py     # Chiffrement authentifié
│   ├── keyring.py  # Gestion des clés
│   └── key_derivation.py # Dérivation de clés
├── storage/        # Persistance des données
│   ├── repository.py # Accès aux données
│   └── schema.py   # Schéma de base de données
├── ui/             # Interfaces utilisateur
│   ├── app_qt.py   # Interface graphique
│   └── cli.py      # Interface ligne de commande
├── tests/          # Tests unitaires
└── tools/          # Utilitaires
```

## 🔐 Sécurité

### Chiffrement
- **Algorithme** : AES-256-GCM (chiffrement authentifié)
- **Dérivation de clés** : Argon2id avec paramètres ajustables
- **Génération aléatoire** : Cryptographiquement sécurisée
- **Gestion mémoire** : Effacement sécurisé des clés en mémoire

### Protection des données
- **Stockage local** : Aucune donnée n'est envoyée sur internet
- **Base chiffrée** : SQLite avec données sensibles chiffrées
- **Verrouillage auto** : Timeout de sécurité configurable
- **Audit de sécurité** : Tests de sécurité intégrés

## 📖 Guide d'utilisation

### Premier démarrage
1. Lancez l'application : `password-manager-gui`
2. Créez votre mot de passe maître (minimum 12 caractères)
3. Confirmez et mémorisez bien ce mot de passe !

### Ajouter un mot de passe
1. Cliquez sur "Ajouter"
2. Remplissez les informations (service, utilisateur, mot de passe)
3. Utilisez le générateur pour créer un mot de passe fort
4. Confirmez l'ajout

### Visualiser un mot de passe
1. Cliquez sur "Voir" dans la liste
2. Entrez votre mot de passe maître si demandé
3. Le mot de passe s'affiche pendant 10 secondes
4. Le vault se verrouille automatiquement

### Recherche
- Tapez dans la barre de recherche
- Recherche en temps réel dans tous les champs
- Résultats instantanés

## 🔧 Configuration

L'application utilise des paramètres de sécurité par défaut optimaux, mais vous pouvez les ajuster :

### Paramètres Argon2 (dans le code)
```python
KDFParams(
    time_cost=2,          # Iterations
    memory_cost=256*1024, # Mémoire en KiB
    parallelism=4,        # Threads parallèles
    hash_len=32          # Longueur de hash
)
```

## 📦 Distribution

### Créer un package
```bash
# Construire le package
python -m build

# Vérifier le package
twine check dist/*

# Publier sur PyPI (test)
twine upload --repository testpypi dist/*

# Publier sur PyPI
twine upload dist/*
```

### Créer un exécutable
```bash
# Installer PyInstaller
pip install pyinstaller

# Créer l'exécutable GUI
pyinstaller --onefile --windowed ui/app_qt.py

# Créer l'exécutable CLI
pyinstaller --onefile ui/cli.py
```

## 🚨 Important

⚠️ **ATTENTION** : Si vous oubliez votre mot de passe maître, vos données seront définitivement perdues. Il n'existe aucun moyen de récupération !

- Choisissez un mot de passe fort mais mémorable
- Considérez l'usage d'une phrase de passe
- Ne partagez jamais votre mot de passe maître
- Sauvegardez régulièrement votre fichier `vault.db`

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment participer :

1. Forkez le projet
2. Créez une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Poussez la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

### Standards de code
- Utilisez `black` pour le formatage
- Suivez les conventions PEP 8
- Ajoutez des tests pour les nouvelles fonctionnalités
- Documentez les fonctions publiques

## 🐛 Signaler un bug

Si vous trouvez un bug, veuillez [ouvrir une issue](https://github.com/marie-angekuitche/password-manager/issues) avec :

- Description détaillée du problème
- Étapes pour reproduire
- Version de Python et OS
- Messages d'erreur complets

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👤 Auteur

**Marie-Ange Kuitche**
- GitHub: [@marie-angekuitche](https://github.com/marie-angekuitche)
- Email: marie-ange@example.com

## 🙏 Remerciements

- [cryptography](https://cryptography.io/) pour les primitives cryptographiques
- [argon2-cffi](https://argon2-cffi.readthedocs.io/) pour la dérivation de clés
- [PySide6](https://doc.qt.io/qtforpython/) pour l'interface graphique
- [SQLite](https://www.sqlite.org/) pour le stockage local

---

⭐ **N'oubliez pas de laisser une étoile si ce projet vous aide !**

# Configuration et Documentation Technique - MaNelly Password Manager

## Vue d'ensemble

MaNelly est un gestionnaire de mots de passe sécurisé développé en Python avec interface graphique Qt. Il utilise un chiffrement AES-256-GCM et une dérivation de clé Argon2id pour assurer la sécurité maximale des données.

## Architecture du Système

### Structure des Modules

```
password-manager/
├── core/               # Logique métier principale
│   ├── vault.py        # Gestion du coffre-fort
│   └── generator.py    # Génération de mots de passe
├── crypto/             # Cryptographie
│   ├── aead.py         # Chiffrement AES-256-GCM
│   ├── key_derivation.py # Dérivation Argon2id
│   └── keyring.py      # Gestion des clés en mémoire
├── storage/            # Persistance des données
│   ├── repository.py   # Opérations base de données
│   └── schema.py       # Schéma SQLite
├── ui/                 # Interface utilisateur
│   ├── app_qt.py       # Application graphique
│   └── cli.py          # Interface ligne de commande
└── tests/              # Tests unitaires
```

### Technologies Utilisées

| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| Interface | PySide6 | 6.5+ | Interface graphique Qt |
| Cryptographie | cryptography | 41.0+ | AES-256-GCM |
| Dérivation clé | argon2-cffi | 23.0+ | Argon2id KDF |
| Base de données | SQLite | 3.x | Stockage persistant |
| Tests | pytest | 7.0+ | Tests unitaires |

## Configuration de Sécurité

### Paramètres Cryptographiques

#### Dérivation de clé (Argon2id)
```python
KDFParams:
    time_cost: 2          # Iterations
    memory_cost: 262144   # 256 MB en KiB
    parallelism: 4        # Threads parallèles
    salt: 16 bytes        # Sel aléatoire
    hash_len: 32          # Clé 256-bit
```

#### Chiffrement (AES-256-GCM)
- **Algorithme** : AES-256-GCM
- **Taille de clé** : 256 bits (32 bytes)
- **Nonce** : 96 bits (12 bytes) généré aléatoirement
- **AAD** : URL du service pour authentification contextuelle

### Validation des Mots de Passe Maîtres

| Critère | Valeur | Description |
|---------|--------|-------------|
| Longueur minimale | 12 caractères | Résistance force brute |
| Types requis | 4 | Majuscules, minuscules, chiffres, spéciaux |
| Patterns interdits | Liste noire | password, 123456, qwerty, etc. |
| Séquences | Détection | Séquences clavier/alphabet |

## Configuration des Données

### Stockage Plateforme

| OS | Chemin de données |
|----|-------------------|
| macOS | `~/Library/Application Support/PasswordManager/` |
| Windows | `%APPDATA%/PasswordManager/` |
| Linux | `~/.local/share/passwordmanager/` |

### Schéma Base de Données

#### Table `entries`
```sql
CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,           -- URL du service
    title TEXT,                  -- Nom affiché
    username TEXT,               -- Nom d'utilisateur
    password_ct BLOB NOT NULL,   -- Mot de passe chiffré
    nonce BLOB NOT NULL,         -- Nonce de chiffrement
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

#### Table `vault_meta`
```sql
CREATE TABLE vault_meta (
    kdf_name TEXT,               -- "argon2id"
    kdf_params TEXT,             -- Paramètres JSON
    salt BLOB,                   -- Sel principal
    verifier BLOB,               -- Hash SHA-256 de la clé
    username TEXT,               -- Nom d'utilisateur du coffre
    version INTEGER,             -- Version du format
    created_at TEXT DEFAULT (datetime('now'))
);
```

## Configuration d'Environnement

### Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `QT_QPA_PLATFORM` | Plateforme Qt | Auto-détection |
| `APPDATA` | Données Windows | `%USERPROFILE%/AppData/Roaming` |
| `HOME` | Répertoire utilisateur | Auto-détection |

### Dépendances Python

```toml
[project]
dependencies = [
    "cryptography>=41.0.0",
    "argon2-cffi>=23.0.0", 
    "PySide6>=6.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "pyinstaller>=6.0.0",
]
```

## Déploiement

### Création du Bundle macOS

```bash
pyinstaller \
    --name="MaNelly" \
    --onefile \
    --windowed \
    --icon=assets/icon.icns \
    --add-data "core:core" \
    --add-data "crypto:crypto" \
    --add-data "storage:storage" \
    --add-data "ui:ui" \
    ui/app_qt.py
```

### Installation Développement

```bash
# Cloner le projet
git clone https://github.com/marie-angekuitche/password-manager.git
cd password-manager

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou venv\Scripts\activate  # Windows

# Installer dépendances
pip install -e ".[dev]"

# Lancer tests
python -m pytest tests/

# Lancer l'application
python ui/app_qt.py
```

## Sécurité et Conformité

### Mesures de Sécurité Implémentées

1. **Chiffrement fort** : AES-256-GCM avec authentification
2. **Dérivation robuste** : Argon2id résistant aux attaques
3. **Nettoyage mémoire** : Effacement sécurisé des clés
4. **Authentification double** : Nom d'utilisateur + mot de passe maître
5. **Isolation processus** : Chaque coffre est indépendant
6. **Auto-verrouillage** : Timeout automatique après consultation
7. **Presse-papiers sécurisé** : Effacement automatique après 30s

### Conformité Standards

- **NIST SP 800-63B** : Recommandations authentification
- **OWASP ASVS** : Standards sécurité applicative
- **PKCS#5** : Dérivation de clé par mot de passe
- **RFC 5084** : Chiffrement authentifié AES-GCM

## Maintenance et Monitoring

### Logs d'Application

L'application utilise les logs Python standard :
- **Niveau INFO** : Opérations normales
- **Niveau WARNING** : Situations suspectes
- **Niveau ERROR** : Erreurs récupérables
- **Niveau CRITICAL** : Erreurs fatales

### Sauvegarde et Récupération

```bash
# Sauvegarder le coffre-fort
cp ~/Library/Application\ Support/PasswordManager/vault.db backup_$(date +%Y%m%d).db

# Restaurer depuis sauvegarde
cp backup_20240924.db ~/Library/Application\ Support/PasswordManager/vault.db
```

### Mise à Jour de Version

1. Télécharger nouvelle version
2. Sauvegarder vault.db existant
3. Installer nouvelle application
4. Vérifier compatibilité base de données
5. Tester fonctionnalités essentielles

## Dépannage

### Problèmes Courants

| Problème | Cause | Solution |
|----------|-------|----------|
| "Unable to open database" | Permissions/chemin | Vérifier droits ~/Library/Application Support/ |
| "Vault verrouillé" | Timeout session | Re-entrer mot de passe maître |
| "Nom d'utilisateur incorrect" | Mauvais utilisateur | Utiliser le nom d'utilisateur enregistré |
| Interface ne s'affiche pas | Problème Qt | Installer/mettre à jour PySide6 |

### Commandes de Diagnostic

```bash
# Vérifier installation
python -c "import ui.app_qt; print('OK')"

# Tester cryptographie
python -c "from crypto import aead; print('Crypto OK')"

# Vérifier base de données
sqlite3 ~/Library/Application\ Support/PasswordManager/vault.db ".schema"
```

---

**Document créé le :** 24 septembre 2025  
**Version :** 1.0  
**Auteur :** Marie-Ange Kuitche

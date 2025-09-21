# 🔐 Gestionnaire de Mots de Passe Sécurisé

## 📖 Description du projet
Application multiplateforme en Python permettant de stocker, organiser et sécuriser des identifiants numériques avec chiffrement AES-256.

**Deadline :** Mercredi 12h30  
**Équipe :** 2 personnes  
**Temps :** 32h de développement

---

## 📁 Structure du Projet

```
password_manager/
├── src/                          # 🐍 Code source principal
│   ├── __init__.py              # Fichier Python package (vide)
│   ├── crypto/                  # 🔒 Module de chiffrement/sécurité
│   │   ├── __init__.py         # Fichier Python package (vide)
│   │   └── encryption.py       # Chiffrement AES-256 + gestion clés
│   ├── database/               # 💾 Module base de données
│   │   ├── __init__.py         # Fichier Python package (vide)
│   │   └── db_manager.py       # Gestion SQLite + CRUD
│   ├── gui/                    # 🖥️ Interface graphique (Tkinter)
│   │   ├── __init__.py         # Fichier Python package (vide)
│   │   ├── main_window.py      # Fenêtre principale de l'app
│   │   └── login_window.py     # Fenêtre connexion mot de passe maître
│   └── utils/                  # 🛠️ Utilitaires
│       ├── __init__.py         # Fichier Python package (vide)
│       └── password_generator.py # Générateur mots de passe personnalisable
├── tests/                      # 🧪 Tests unitaires et d'intégration
├── docs/                       # 📚 Documentation utilisateur/technique
├── config/                     # ⚙️ Fichiers de configuration
├── requirements.txt            # 📦 Dépendances Python
├── setup.py                   # 🔧 Script d'installation
└── README.md                  # 📖 Ce fichier
```

---

## 📋 Rôle de Chaque Fichier

### 🔒 **src/crypto/encryption.py**
**Responsabilité :** Sécurité et chiffrement  
**Contient :**
- `chiffrer_aes256(data, master_password)` → Chiffre les mots de passe
- `dechiffrer_aes256(encrypted_data, master_password)` → Déchiffre les mots de passe
- `generer_cle_depuis_master(master_password)` → Dérive la clé de chiffrement
- `valider_mot_de_passe_maitre(password)` → Vérifie robustesse (min caractères)

### 💾 **src/database/db_manager.py**
**Responsabilité :** Gestion base de données SQLite  
**Contient :**
- `creer_base_donnees()` → Initialise les tables SQLite
- `ajouter_mot_de_passe(site_name, url, username, password)` → Sauvegarde nouvelle entrée
- `recuperer_mot_de_passe(site_name)` → Récupère mot de passe pour un site
- `supprimer_mot_de_passe(id)` → Supprime une entrée
- `rechercher_par_site(terme)` → Recherche dans la barre de recherche
- `exporter_donnees()` / `importer_donnees()` → Export/import sécurisé

### 🖥️ **src/gui/login_window.py**
**Responsabilité :** Fenêtre de connexion  
**Contient :**
- Interface de saisie du mot de passe maître
- Validation du mot de passe (robustesse + authentification)
- Transition vers la fenêtre principale si OK
- Gestion des erreurs de connexion

### 🖥️ **src/gui/main_window.py**
**Responsabilité :** Interface principale de l'application  
**Contient :**
- **Barre de recherche** pour accéder aux mots de passe
- **Liste des sites** avec **nom en évidence** (cahier des charges)
- **Boutons :** Ajouter, Modifier, Supprimer
- **Formulaires :** Ajout/modification d'entrées (URL + mot de passe)
- **Intégration générateur** de mots de passe
- **Verrouillage automatique** après inactivité
- **Export/Import** des données

### 🛠️ **src/utils/password_generator.py**
**Responsabilité :** Générateur de mots de passe  
**Contient :**
- `generer_mot_de_passe(longueur, majuscules, chiffres, symboles)` → Générateur personnalisable
- `evaluer_force_mot_de_passe(password)` → Évalue la robustesse
- Interface de configuration (longueur, types de caractères)

---

## 🎯 Fonctionnalités à Implémenter

### ✅ Fonctions Principales (Cahier des charges)
- [ ] **Mot de passe maître robuste** (minimum caractères imposé)
- [ ] **Ajouter URL + mot de passe** (nom du site en évidence)
- [ ] **Récupérer mots de passe hachés** assignés à une URL
- [ ] **Supprimer un mot de passe**
- [ ] **Barre de recherche** pour accéder au mot de passe souhaité
- [ ] **Générateur personnalisable**

### 🔒 Sécurité (Cahier des charges)
- [ ] **Chiffrement AES-256** des données locales
- [ ] **Mot de passe maître**
- [ ] **Verrouillage automatique** après inactivité
- [ ] **Export/import sécurisé** des données

---

## 🚀 Étapes de Développement

### **Phase 1 : Setup & Architecture (4h)**
- [x] Structure projet créée
- [ ] Environnement virtuel + dépendances
- [ ] GitHub Actions CI/CD
- [ ] Architecture modules définie

### **Phase 2 : Backend Core (12-14h)**
- [ ] Implémentation chiffrement AES-256
- [ ] Base de données SQLite + CRUD
- [ ] Générateur de mots de passe
- [ ] Tests sécurité

### **Phase 3 : Interface Utilisateur (8-10h)**
- [ ] Fenêtre de connexion
- [ ] Interface principale (recherche, liste, formulaires)
- [ ] Intégration frontend-backend
- [ ] Tests utilisateur

### **Phase 4 : Finalisation (6h)**
- [ ] Application installable
- [ ] Documentation complète
- [ ] Tests finaux
- [ ] Livrables

---

## 📦 Installation & Lancement

```bash
# 1. Cloner le projet
git clone [votre-repo]
cd password_manager

# 2. Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# ou venv\Scripts\activate  # Windows

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Lancer l'application
python src/gui/login_window.py
```

---

## 📚 Livrables Attendus (Mercredi 12h30)
- [ ] **Application installable**
- [ ] **Fichier de configuration** et documentation technique
- [ ] **Guide utilisateur** (Markdown + PDF)
- [ ] **Rapport de tests**
- [ ] **Cahier de recette**

---

## 👥 Répartition des Tâches

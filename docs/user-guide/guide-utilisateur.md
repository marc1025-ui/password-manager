# Guide Utilisateur - MaNelly Password Manager

## Table des matières

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Premier démarrage](#premier-démarrage)
4. [Utilisation quotidienne](#utilisation-quotidienne)
5. [Fonctionnalités avancées](#fonctionnalités-avancées)
6. [Sécurité](#sécurité)
7. [Dépannage](#dépannage)

## Introduction

**MaNelly** est votre gestionnaire de mots de passe personnel et sécurisé. Il vous permet de :

- 🔒 **Stocker** tous vos mots de passe de façon chiffrée
- 🎲 **Générer** des mots de passe forts automatiquement
- 🔍 **Rechercher** rapidement vos comptes
- 📋 **Copier** facilement vos mots de passe
- 🛡️ **Protéger** vos données avec un chiffrement militaire

### Pourquoi utiliser MaNelly ?

- ✅ **Sécurité maximale** : Chiffrement AES-256 + Argon2id
- ✅ **Facilité d'usage** : Interface moderne et intuitive
- ✅ **Confidentialité** : Vos données restent sur votre ordinateur
- ✅ **Gratuit** : Aucun abonnement, aucune limite

## Installation

### Téléchargement

1. Téléchargez `MaNelly.app` depuis le dossier `dist/`
2. Glissez l'application dans votre dossier `Applications`
3. Double-cliquez pour lancer MaNelly

### Première ouverture sur macOS

Si macOS affiche "L'application ne peut pas être ouverte" :

1. **Clic droit** sur MaNelly.app → **Ouvrir**
2. Cliquez **"Ouvrir"** dans la boîte de dialogue
3. MaNelly se lancera et sera autorisé pour le futur

## Premier démarrage

### Création de votre compte

À la première ouverture, MaNelly vous demande de créer votre compte :

![Écran d'inscription](screenshots/signup.png)

1. **Nom d'utilisateur** : Choisissez un nom que vous retiendrez
2. **Mot de passe maître** : Créez un mot de passe TRÈS fort
   - Au moins 12 caractères
   - Majuscules + minuscules + chiffres + symboles
   - Évitez les mots du dictionnaire
3. **Confirmer** : Retapez le mot de passe identique

### ⚠️ IMPORTANT - Mot de passe maître

> **Si vous oubliez votre mot de passe maître, vous perdrez DÉFINITIVEMENT accès à tous vos mots de passe !**
> 
> **Conseils :**
> - Écrivez-le sur papier et gardez-le en lieu sûr
> - Utilisez une phrase de passe mémorable : "MonChien2024!Aime$LesBiscuits"
> - Ne le stockez JAMAIS sur votre ordinateur

## Utilisation quotidienne

### Interface principale

![Interface principale](screenshots/main-window.png)

L'interface se compose de :

1. **Barre de recherche** : Tapez pour filtrer vos comptes
2. **Tableau des mots de passe** : Liste de tous vos comptes
3. **Bouton "Ajouter"** : Créer un nouveau compte
4. **Actions** : "Voir" et "Supprimer" pour chaque entrée

### Ajouter un nouveau mot de passe

1. Cliquez sur **"Ajouter"**
2. Remplissez le formulaire :
   - **Service** : Nom du site/service (ex: "Gmail")
   - **Utilisateur** : Votre nom d'utilisateur/email
   - **Mot de passe** : Tapez ou générez automatiquement
   - **URL** : Adresse du site (ex: "https://gmail.com")
   - **Notes** : Informations supplémentaires (optionnel)

![Formulaire d'ajout](screenshots/add-password.png)

3. Cliquez **"OK"** pour sauvegarder

### Générer un mot de passe fort

1. Dans le formulaire d'ajout, cliquez **"Générer un mot de passe"**
2. Configurez vos préférences :
   - **Longueur** : 16 caractères recommandés
   - **Types** : Gardez tout coché pour maximum de sécurité
3. Cliquez **"Générer"** jusqu'à obtenir un mot de passe qui vous plaît
4. Cliquez **"Utiliser ce mot de passe"**

![Générateur de mots de passe](screenshots/generator.png)

### Consulter un mot de passe

1. Trouvez votre compte dans la liste (utilisez la recherche si besoin)
2. Cliquez **"Voir"** dans la colonne Actions
3. Entrez votre **mot de passe maître** si demandé
4. Consultez les détails affichés

![Détails d'un mot de passe](screenshots/view-password.png)

### Copier un mot de passe

1. Dans la fenêtre de détails, cliquez **"📋 Copier le mot de passe"**
2. Le mot de passe est copié dans votre presse-papiers
3. Utilisez **Cmd+V** (macOS) pour le coller où vous voulez
4. **Sécurité** : Le presse-papiers se vide automatiquement après 30 secondes

### Rechercher un compte

Tapez dans la barre de recherche pour filtrer par :
- **Nom du service** (ex: "google")
- **Nom d'utilisateur** (ex: "marie@gmail.com")
- **URL** (ex: "facebook.com")

La recherche fonctionne en temps réel !

### Supprimer un compte

1. Cliquez **"Supprimer"** sur la ligne du compte
2. Confirmez la suppression
3. ⚠️ **La suppression est définitive !**

## Fonctionnalités avancées

### Verrouillage automatique

MaNelly se verrouille automatiquement après consultation d'un mot de passe pour votre sécurité. Vous devrez re-entrer votre mot de passe maître pour la prochaine consultation.

### Gestion de plusieurs profils

Chaque nom d'utilisateur créé un coffre-fort indépendant. Impossible d'accéder au coffre d'un autre utilisateur même en connaissant son mot de passe maître.

### Sauvegarde manuelle

Vos données sont stockées dans :
```
~/Library/Application Support/PasswordManager/vault.db
```

Pour sauvegarder :
```bash
cp ~/Library/Application\ Support/PasswordManager/vault.db ~/Desktop/ma-sauvegarde-$(date +%Y%m%d).db
```

## Sécurité

### Bonnes pratiques

#### Mot de passe maître
- ✅ Utilisez une phrase de passe longue et mémorable
- ✅ Incluez majuscules, minuscules, chiffres, symboles
- ❌ Ne le partagez avec personne
- ❌ Ne l'écrivez pas dans un fichier informatique

#### Mots de passe générés
- ✅ Utilisez le générateur intégré pour tous vos comptes
- ✅ Longueur minimum 12 caractères, 16+ recommandés
- ✅ Acceptez tous les types de caractères
- ❌ Ne réutilisez jamais le même mot de passe

#### Utilisation générale
- ✅ Fermez MaNelly quand vous ne l'utilisez pas
- ✅ Verrouillez votre session macOS
- ✅ Sauvegardez régulièrement votre coffre-fort
- ❌ N'utilisez pas MaNelly sur un ordinateur public

### Que fait MaNelly pour votre sécurité

1. **Chiffrement militaire** : Vos mots de passe sont chiffrés avec AES-256
2. **Dérivation robuste** : Argon2id rend le piratage extrêmement difficile
3. **Authentification double** : Nom d'utilisateur + mot de passe maître
4. **Nettoyage mémoire** : Les clés sont effacées de la RAM
5. **Presse-papiers sécurisé** : Auto-effacement après 30 secondes
6. **Isolation** : Impossible d'accéder aux données d'un autre utilisateur

## Dépannage

### Problèmes fréquents

#### "J'ai oublié mon mot de passe maître"
❌ **Il n'y a aucun moyen de récupérer vos données.** C'est volontaire pour votre sécurité.
**Solution** : Supprimer `vault.db` et recréer un coffre-fort (vous perdrez tout).

#### "Nom d'utilisateur incorrect"
✅ **Utilisez le nom exact** que vous aviez créé lors de l'inscription.
Le nom d'utilisateur est sensible à la casse.

#### "L'application ne se lance pas"
✅ **Solutions** :
- Redémarrez votre Mac
- Vérifiez que l'app est dans `/Applications/`
- Essayez clic droit → Ouvrir

#### "Erreur lors de l'initialisation"
✅ **Solutions** :
- Vérifiez les permissions du dossier `~/Library/Application Support/`
- Relancez l'application
- Si le problème persiste, supprimez le dossier `PasswordManager/`

### Réinitialisation complète

Si vous voulez repartir à zéro :

```bash
rm -rf ~/Library/Application\ Support/PasswordManager/
```

**⚠️ Attention : Cela supprime TOUS vos mots de passe !**

### Support technique

Pour signaler un bug ou demander de l'aide :
- 📧 **Email** : marie-ange.kuitche@example.com
- 💻 **GitHub** : https://github.com/marie-angekuitche/password-manager

## Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| **Cmd+F** | Aller à la recherche |
| **Cmd+N** | Ajouter nouveau mot de passe |
| **Cmd+V** | Coller (après copie) |
| **Espace** | Voir le mot de passe sélectionné |
| **Suppr** | Supprimer le mot de passe sélectionné |

---

**Guide créé le :** 24 septembre 2025  
**Version MaNelly :** 1.0  
**Auteur :** Marie-Ange Kuitche

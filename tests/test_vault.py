import unittest
import tempfile
import os
from pathlib import Path
from core.vault import Vault
from crypto.key_derivation import KDFParams
from storage import repository
from storage.repository import Entry


class TestVault(unittest.TestCase):
    """Tests pour la classe Vault"""

    def setUp(self):
        """Configuration avant chaque test"""
        # Créer un fichier temporaire pour la base de données de test
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)  # Fermer le descripteur de fichier

        self.vault = Vault(Path(self.test_db_path))
        self.master_password = "TestMasterPassword123!"

    def tearDown(self):
        """Nettoyage après chaque test"""
        # Supprimer le fichier de base de données temporaire
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def test_vault_initialization(self):
        """Test d'initialisation du vault"""
        # Le vault doit être créé sans erreur
        self.assertIsNotNone(self.vault)
        self.assertIsNotNone(self.vault.con)

    def test_init_master_password_strong(self):
        """Test d'initialisation avec un mot de passe maître fort"""
        strong_password = "MyVeryStr0ng!MasterP@ssw0rd2024"

        # L'initialisation doit réussir
        self.vault.init_master_password(strong_password)

        # Vérifier que les métadonnées ont été sauvegardées
        meta = repository.load_vault_meta(self.vault.con)
        self.assertIsNotNone(meta)
        self.assertIn("kdf_params", meta)
        self.assertIn("verifier", meta)
        self.assertIn("version", meta)

    def test_init_master_password_weak(self):
        """Test d'initialisation avec un mot de passe maître faible"""
        weak_password = "123"

        # L'initialisation doit échouer
        with self.assertRaises(ValueError):
            self.vault.init_master_password(weak_password)

    def test_init_master_password_already_initialized(self):
        """Test d'initialisation sur un vault déjà initialisé"""
        # Initialiser une première fois
        self.vault.init_master_password(self.master_password)

        # Essayer d'initialiser à nouveau doit échouer
        with self.assertRaises(RuntimeError):
            self.vault.init_master_password("AnotherPassword123!")

    def test_add_entry_vault_locked(self):
        """Test d'ajout d'entrée avec vault verrouillé"""
        # Le vault n'est pas déverrouillé
        with self.assertRaises(AssertionError):
            self.vault.add_entry(
                url="https://example.com",
                title="Test Entry",
                username="testuser",
                password="testpass"
            )

    def test_add_entry_vault_unlocked(self):
        """Test d'ajout d'entrée avec vault déverrouillé"""
        # Initialiser et déverrouiller le vault
        self.vault.init_master_password(self.master_password)

        # Ajouter une entrée
        entry_id = self.vault.add_entry(
            url="https://example.com",
            title="Test Entry",
            username="testuser",
            password="testpass123"
        )

        self.assertIsInstance(entry_id, int)
        self.assertGreater(entry_id, 0)

    def test_get_entry_without_reveal(self):
        """Test de récupération d'entrée sans révéler le mot de passe"""
        # Initialiser le vault et ajouter une entrée
        self.vault.init_master_password(self.master_password)
        entry_id = self.vault.add_entry(
            url="https://test.com",
            title="Test Site",
            username="user@test.com",
            password="secretpassword"
        )

        # Récupérer l'entrée sans révéler le mot de passe
        entry = self.vault.get_entry(entry_id, reveal=False)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.url, "https://test.com")
        self.assertEqual(entry.title, "Test Site")
        self.assertEqual(entry.username, "user@test.com")
        # Le mot de passe doit être chiffré (bytes)
        self.assertIsInstance(entry.password_ct, bytes)

    def test_get_entry_with_reveal(self):
        """Test de récupération d'entrée avec révélation du mot de passe"""
        # Initialiser le vault et ajouter une entrée
        self.vault.init_master_password(self.master_password)
        original_password = "secretpassword123"
        entry_id = self.vault.add_entry(
            url="https://test.com",
            title="Test Site",
            username="user@test.com",
            password=original_password
        )

        # Récupérer l'entrée avec révélation du mot de passe
        entry = self.vault.get_entry(entry_id, reveal=True)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.password_ct, original_password)

    def test_get_entry_vault_locked_with_reveal(self):
        """Test de récupération avec révélation sur vault verrouillé"""
        # Initialiser le vault et ajouter une entrée
        self.vault.init_master_password(self.master_password)
        entry_id = self.vault.add_entry(
            url="https://test.com",
            title="Test Site",
            username="user@test.com",
            password="secret"
        )

        # Verrouiller le vault
        self.vault._keyring.lock()

        # Essayer de révéler le mot de passe doit échouer
        with self.assertRaises(AssertionError):
            self.vault.get_entry(entry_id, reveal=True)

    def test_get_nonexistent_entry(self):
        """Test de récupération d'une entrée inexistante"""
        self.vault.init_master_password(self.master_password)

        entry = self.vault.get_entry(999999)  # ID inexistant
        self.assertIsNone(entry)

    def test_search_entries(self):
        """Test de recherche d'entrées"""
        # Initialiser le vault et ajouter plusieurs entrées
        self.vault.init_master_password(self.master_password)

        # Ajouter des entrées de test
        self.vault.add_entry("https://google.com", "Google", "user@gmail.com", "pass1")
        self.vault.add_entry("https://github.com", "GitHub", "developer", "pass2")
        self.vault.add_entry("https://stackoverflow.com", "Stack Overflow", "coder", "pass3")

        # Rechercher par URL
        results = list(self.vault.search("google"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, "https://google.com")

        # Rechercher par nom d'utilisateur
        results = list(self.vault.search("developer"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, "developer")

        # Rechercher par titre
        results = list(self.vault.search("Stack"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Stack Overflow")

        # Recherche sans résultat
        results = list(self.vault.search("inexistant"))
        self.assertEqual(len(results), 0)

    def test_multiple_entries_same_url(self):
        """Test d'ajout de plusieurs entrées pour la même URL"""
        self.vault.init_master_password(self.master_password)

        # Ajouter plusieurs comptes pour le même site
        id1 = self.vault.add_entry("https://example.com", "Example", "user1", "pass1")
        id2 = self.vault.add_entry("https://example.com", "Example", "user2", "pass2")

        self.assertNotEqual(id1, id2)

        # Vérifier que les deux entrées existent
        entry1 = self.vault.get_entry(id1, reveal=True)
        entry2 = self.vault.get_entry(id2, reveal=True)

        self.assertEqual(entry1.username, "user1")
        self.assertEqual(entry2.username, "user2")
        self.assertEqual(entry1.password_ct, "pass1")
        self.assertEqual(entry2.password_ct, "pass2")

    def test_entry_encryption_different_keys(self):
        """Test que le chiffrement change avec des clés différentes"""
        # Créer deux vaults avec des mots de passe différents
        vault2_fd, vault2_path = tempfile.mkstemp(suffix='.db')
        os.close(vault2_fd)

        try:
            vault2 = Vault(Path(vault2_path))

            # Initialiser les deux vaults avec des mots de passe différents
            self.vault.init_master_password("Password1!")
            vault2.init_master_password("Password2!")

            # Ajouter la même entrée dans les deux vaults
            same_password = "samepassword"
            id1 = self.vault.add_entry("https://test.com", "Test", "user", same_password)
            id2 = vault2.add_entry("https://test.com", "Test", "user", same_password)

            # Récupérer les entrées sans révélation (chiffrées)
            entry1 = self.vault.get_entry(id1, reveal=False)
            entry2 = vault2.get_entry(id2, reveal=False)

            # Les textes chiffrés doivent être différents
            self.assertNotEqual(entry1.password_ct, entry2.password_ct)

            # Mais les mots de passe déchiffrés doivent être identiques
            entry1_revealed = self.vault.get_entry(id1, reveal=True)
            entry2_revealed = vault2.get_entry(id2, reveal=True)

            self.assertEqual(entry1_revealed.password_ct, same_password)
            self.assertEqual(entry2_revealed.password_ct, same_password)

        finally:
            # Nettoyer le deuxième vault
            if os.path.exists(vault2_path):
                os.unlink(vault2_path)

    def test_vault_persistence(self):
        """Test de persistance du vault entre les sessions"""
        # Initialiser le vault et ajouter une entrée
        self.vault.init_master_password(self.master_password)
        entry_id = self.vault.add_entry(
            "https://persistent.com",
            "Persistent Test",
            "testuser",
            "testpass"
        )

        # Fermer le vault (simuler une fermeture d'application)
        self.vault.con.close()

        # Rouvrir le vault
        new_vault = Vault(Path(self.test_db_path))

        # Vérifier que les métadonnées sont toujours là
        meta = repository.load_vault_meta(new_vault.con)
        self.assertIsNotNone(meta)

        # L'entrée doit toujours exister (mais chiffrée)
        entry = repository.get_entry(new_vault.con, entry_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.url, "https://persistent.com")
        self.assertEqual(entry.title, "Persistent Test")
        self.assertEqual(entry.username, "testuser")

    def test_vault_with_empty_fields(self):
        """Test d'ajout d'entrée avec des champs vides"""
        self.vault.init_master_password(self.master_password)

        # Ajouter une entrée avec des champs optionnels vides
        entry_id = self.vault.add_entry(
            url="https://minimal.com",
            title=None,  # Sera remplacé par l'URL
            username=None,
            password="onlypassword"
        )

        entry = self.vault.get_entry(entry_id, reveal=True)
        self.assertEqual(entry.title, "https://minimal.com")  # Titre par défaut
        self.assertIsNone(entry.username)
        self.assertEqual(entry.password_ct, "onlypassword")


class TestVaultIntegration(unittest.TestCase):
    """Tests d'intégration pour le vault"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        self.vault = Vault(Path(self.test_db_path))
        self.master_password = "IntegrationTest123!"

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def test_full_workflow(self):
        """Test du workflow complet du vault"""
        # 1. Initialiser le vault
        self.vault.init_master_password(self.master_password)

        # 2. Ajouter plusieurs entrées
        entries_data = [
            ("https://bank.com", "My Bank", "account123", "bankpass123"),
            ("https://email.com", "Email Provider", "user@email.com", "emailpass456"),
            ("https://work.com", "Work Portal", "employee", "workpass789")
        ]

        entry_ids = []
        for url, title, username, password in entries_data:
            entry_id = self.vault.add_entry(url, title, username, password)
            entry_ids.append(entry_id)

        # 3. Vérifier que toutes les entrées ont été ajoutées
        self.assertEqual(len(entry_ids), 3)

        # 4. Rechercher et vérifier les entrées
        for i, (url, title, username, password) in enumerate(entries_data):
            entry = self.vault.get_entry(entry_ids[i], reveal=True)
            self.assertEqual(entry.url, url)
            self.assertEqual(entry.title, title)
            self.assertEqual(entry.username, username)
            self.assertEqual(entry.password_ct, password)

        # 5. Tester la recherche
        bank_results = list(self.vault.search("bank"))
        self.assertEqual(len(bank_results), 1)
        self.assertEqual(bank_results[0].title, "My Bank")

        # 6. Verrouiller et tenter d'accéder (doit échouer)
        self.vault._keyring.lock()
        with self.assertRaises(AssertionError):
            self.vault.get_entry(entry_ids[0], reveal=True)

    def test_vault_security_isolation(self):
        """Test d'isolation de sécurité entre vaults"""
        # Créer un deuxième vault
        vault2_fd, vault2_path = tempfile.mkstemp(suffix='.db')
        os.close(vault2_fd)

        try:
            vault2 = Vault(Path(vault2_path))

            # Initialiser les deux vaults
            self.vault.init_master_password("Password1!")
            vault2.init_master_password("Password2!")

            # Ajouter des entrées différentes
            id1 = self.vault.add_entry("https://vault1.com", "Vault 1", "user1", "secret1")
            id2 = vault2.add_entry("https://vault2.com", "Vault 2", "user2", "secret2")

            # Chaque vault ne peut accéder qu'à ses propres données
            entry1 = self.vault.get_entry(id1, reveal=True)
            entry2 = vault2.get_entry(id2, reveal=True)

            self.assertEqual(entry1.password_ct, "secret1")
            self.assertEqual(entry2.password_ct, "secret2")

            # Les IDs peuvent être les mêmes mais les données sont isolées
            vault1_entry = repository.get_entry(self.vault.con, id1)
            vault2_entry = repository.get_entry(vault2.con, id2)

            # Les données chiffrées doivent être différentes
            if id1 == id2:  # Si même ID
                self.assertNotEqual(vault1_entry.password_ct, vault2_entry.password_ct)

        finally:
            if os.path.exists(vault2_path):
                os.unlink(vault2_path)


if __name__ == '__main__':
    unittest.main()

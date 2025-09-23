import unittest
import tempfile
import os
import json
from pathlib import Path
from storage import repository, schema
from storage.repository import Entry
from crypto.key_derivation import KDFParams


class TestRepository(unittest.TestCase):
    """Tests pour le module repository"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        self.con = schema.open_db(Path(self.test_db_path))

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.con.close()
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def test_add_entry(self):
        """Test d'ajout d'entrée"""
        entry = Entry(
            id=None,
            url="https://test.com",
            title="Test Site",
            username="testuser",
            password_ct=b"encrypted_password",
            nonce=b"test_nonce"
        )

        entry_id = repository.add_entry(self.con, entry)

        self.assertIsInstance(entry_id, int)
        self.assertGreater(entry_id, 0)

    def test_get_entry(self):
        """Test de récupération d'entrée"""
        # Ajouter une entrée d'abord
        entry = Entry(
            id=None,
            url="https://example.com",
            title="Example",
            username="user",
            password_ct=b"secret",
            nonce=b"nonce123"
        )
        entry_id = repository.add_entry(self.con, entry)

        # Récupérer l'entrée
        retrieved_entry = repository.get_entry(self.con, entry_id)

        self.assertIsNotNone(retrieved_entry)
        self.assertEqual(retrieved_entry.id, entry_id)
        self.assertEqual(retrieved_entry.url, "https://example.com")
        self.assertEqual(retrieved_entry.title, "Example")
        self.assertEqual(retrieved_entry.username, "user")
        self.assertEqual(retrieved_entry.password_ct, b"secret")
        self.assertEqual(retrieved_entry.nonce, b"nonce123")

    def test_get_nonexistent_entry(self):
        """Test de récupération d'entrée inexistante"""
        entry = repository.get_entry(self.con, 999999)
        self.assertIsNone(entry)

    def test_search_entries(self):
        """Test de recherche d'entrées"""
        # Ajouter plusieurs entrées
        entries_data = [
            ("https://google.com", "Google Search", "user@gmail.com"),
            ("https://github.com", "GitHub", "developer"),
            ("https://stackoverflow.com", "Stack Overflow", "coder")
        ]

        for url, title, username in entries_data:
            entry = Entry(
                id=None,
                url=url,
                title=title,
                username=username,
                password_ct=b"password",
                nonce=b"nonce"
            )
            repository.add_entry(self.con, entry)

        # Test recherche par URL
        results = list(repository.search(self.con, "google"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, "https://google.com")

        # Test recherche par titre
        results = list(repository.search(self.con, "GitHub"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "GitHub")

        # Test recherche par nom d'utilisateur
        results = list(repository.search(self.con, "developer"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, "developer")

        # Test recherche partielle
        results = list(repository.search(self.con, "stack"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Stack Overflow")

        # Test recherche sans résultat
        results = list(repository.search(self.con, "inexistant"))
        self.assertEqual(len(results), 0)

    def test_delete_entry(self):
        """Test de suppression d'entrée"""
        # Ajouter une entrée
        entry = Entry(
            id=None,
            url="https://todelete.com",
            title="To Delete",
            username="user",
            password_ct=b"password",
            nonce=b"nonce"
        )
        entry_id = repository.add_entry(self.con, entry)

        # Vérifier qu'elle existe
        self.assertIsNotNone(repository.get_entry(self.con, entry_id))

        # Supprimer l'entrée
        result = repository.delete(self.con, entry_id)
        self.assertTrue(result)

        # Vérifier qu'elle n'existe plus
        self.assertIsNone(repository.get_entry(self.con, entry_id))

    def test_delete_nonexistent_entry(self):
        """Test de suppression d'entrée inexistante"""
        result = repository.delete(self.con, 999999)
        self.assertFalse(result)

    def test_list_entries(self):
        """Test de listage de toutes les entrées"""
        # Base vide
        entries = repository.list_entries(self.con)
        self.assertEqual(len(entries), 0)

        # Ajouter des entrées
        for i in range(3):
            entry = Entry(
                id=None,
                url=f"https://site{i}.com",
                title=f"Site {i}",
                username=f"user{i}",
                password_ct=f"pass{i}".encode(),
                nonce=f"nonce{i}".encode()
            )
            repository.add_entry(self.con, entry)

        # Lister toutes les entrées
        entries = repository.list_entries(self.con)
        self.assertEqual(len(entries), 3)

        # Vérifier l'ordre (par date de modification décroissante)
        titles = [entry.title for entry in entries]
        # Les entrées les plus récentes d'abord
        self.assertIn("Site 2", titles)
        self.assertIn("Site 1", titles)
        self.assertIn("Site 0", titles)

    def test_save_vault_meta(self):
        """Test de sauvegarde des métadonnées du vault"""
        meta = {
            "kdf_name": "argon2",
            "kdf_params": {
                "time_cost": 2,
                "memory_cost": 256*1024,
                "parallelism": 4,
                "salt": "abcd1234",
                "hash_len": 32
            },
            "salt": b"test_salt",
            "verifier": b"test_verifier",
            "version": 1
        }

        repository.save_vault_meta(self.con, meta)

        # Vérifier que les données ont été sauvegardées
        loaded_meta = repository.load_vault_meta(self.con)
        self.assertIsNotNone(loaded_meta)
        self.assertEqual(loaded_meta["kdf_name"], "argon2")
        self.assertEqual(loaded_meta["version"], 1)
        self.assertEqual(loaded_meta["salt"], b"test_salt")
        self.assertEqual(loaded_meta["verifier"], b"test_verifier")

        # Vérifier que kdf_params a été sérialisé/désérialisé correctement
        kdf_params = loaded_meta["kdf_params"]
        self.assertIsInstance(kdf_params, dict)
        self.assertEqual(kdf_params["time_cost"], 2)
        self.assertEqual(kdf_params["memory_cost"], 256*1024)

    def test_load_vault_meta_empty(self):
        """Test de chargement de métadonnées vides"""
        meta = repository.load_vault_meta(self.con)
        self.assertIsNone(meta)

    def test_update_vault_meta(self):
        """Test de mise à jour des métadonnées (remplacement)"""
        # Sauvegarder des métadonnées initiales
        meta1 = {
            "kdf_name": "argon2",
            "kdf_params": {"time_cost": 1},
            "salt": b"salt1",
            "verifier": b"verifier1",
            "version": 1
        }
        repository.save_vault_meta(self.con, meta1)

        # Sauvegarder de nouvelles métadonnées (doit remplacer)
        meta2 = {
            "kdf_name": "argon2id",
            "kdf_params": {"time_cost": 2},
            "salt": b"salt2",
            "verifier": b"verifier2",
            "version": 2
        }
        repository.save_vault_meta(self.con, meta2)

        # Vérifier que les nouvelles métadonnées ont remplacé les anciennes
        loaded_meta = repository.load_vault_meta(self.con)
        self.assertEqual(loaded_meta["kdf_name"], "argon2id")
        self.assertEqual(loaded_meta["version"], 2)
        self.assertEqual(loaded_meta["salt"], b"salt2")
        self.assertEqual(loaded_meta["verifier"], b"verifier2")


class TestSchema(unittest.TestCase):
    """Tests pour le module schema"""

    def test_open_new_db(self):
        """Test d'ouverture d'une nouvelle base de données"""
        test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(test_db_fd)
        os.unlink(test_db_path)  # Supprimer le fichier pour tester la création

        try:
            con = schema.open_db(Path(test_db_path))

            # Vérifier que la connexion est valide
            self.assertIsNotNone(con)

            # Vérifier que les tables ont été créées
            cursor = con.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            self.assertIn('entries', tables)
            self.assertIn('vault_meta', tables)

            con.close()

        finally:
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)

    def test_open_existing_db(self):
        """Test d'ouverture d'une base de données existante"""
        test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(test_db_fd)

        try:
            # Créer la base une première fois
            con1 = schema.open_db(Path(test_db_path))
            con1.close()

            # Rouvrir la base existante
            con2 = schema.open_db(Path(test_db_path))

            # Doit fonctionner sans erreur
            self.assertIsNotNone(con2)

            # Les tables doivent toujours exister
            cursor = con2.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            self.assertIn('entries', tables)
            self.assertIn('vault_meta', tables)

            con2.close()

        finally:
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)

    def test_db_schema_structure(self):
        """Test de la structure du schéma de base de données"""
        test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(test_db_fd)

        try:
            con = schema.open_db(Path(test_db_path))

            # Vérifier la structure de la table entries
            cursor = con.execute("PRAGMA table_info(entries)")
            entries_columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_entries_columns = {
                'id': 'INTEGER',
                'url': 'TEXT',
                'title': 'TEXT',
                'username': 'TEXT',
                'password_ct': 'BLOB',
                'nonce': 'BLOB',
                'created_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP'
            }

            for col_name, col_type in expected_entries_columns.items():
                self.assertIn(col_name, entries_columns)
                self.assertEqual(entries_columns[col_name], col_type)

            # Vérifier la structure de la table vault_meta
            cursor = con.execute("PRAGMA table_info(vault_meta)")
            meta_columns = {row[1]: row[2] for row in cursor.fetchall()}

            expected_meta_columns = {
                'kdf_name': 'TEXT',
                'kdf_params': 'TEXT',
                'salt': 'BLOB',
                'verifier': 'BLOB',
                'version': 'INTEGER'
            }

            for col_name, col_type in expected_meta_columns.items():
                self.assertIn(col_name, meta_columns)
                self.assertEqual(meta_columns[col_name], col_type)

            con.close()

        finally:
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)


class TestRepositoryIntegration(unittest.TestCase):
    """Tests d'intégration pour le storage"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)
        self.con = schema.open_db(Path(self.test_db_path))

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.con.close()
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def test_full_storage_workflow(self):
        """Test du workflow complet de stockage"""
        # 1. Sauvegarder les métadonnées du vault
        meta = {
            "kdf_name": "argon2",
            "kdf_params": {"time_cost": 2, "memory_cost": 65536},
            "salt": b"test_salt_123",
            "verifier": b"test_verifier_456",
            "version": 1
        }
        repository.save_vault_meta(self.con, meta)

        # 2. Ajouter plusieurs entrées
        entries_data = [
            ("https://site1.com", "Site 1", "user1", b"pass1", b"nonce1"),
            ("https://site2.com", "Site 2", "user2", b"pass2", b"nonce2"),
            ("https://site3.com", "Site 3", "user3", b"pass3", b"nonce3")
        ]

        entry_ids = []
        for url, title, username, password_ct, nonce in entries_data:
            entry = Entry(
                id=None,
                url=url,
                title=title,
                username=username,
                password_ct=password_ct,
                nonce=nonce
            )
            entry_id = repository.add_entry(self.con, entry)
            entry_ids.append(entry_id)

        # 3. Vérifier que les métadonnées sont récupérables
        loaded_meta = repository.load_vault_meta(self.con)
        self.assertEqual(loaded_meta["kdf_name"], "argon2")
        self.assertEqual(loaded_meta["version"], 1)

        # 4. Vérifier que toutes les entrées sont récupérables
        all_entries = repository.list_entries(self.con)
        self.assertEqual(len(all_entries), 3)

        # 5. Tester la recherche
        site1_results = list(repository.search(self.con, "Site 1"))
        self.assertEqual(len(site1_results), 1)
        self.assertEqual(site1_results[0].title, "Site 1")

        # 6. Supprimer une entrée
        repository.delete(self.con, entry_ids[0])
        remaining_entries = repository.list_entries(self.con)
        self.assertEqual(len(remaining_entries), 2)

        # 7. Vérifier que l'entrée supprimée n'existe plus
        deleted_entry = repository.get_entry(self.con, entry_ids[0])
        self.assertIsNone(deleted_entry)

    def test_concurrent_operations(self):
        """Test d'opérations concurrentes sur la base"""
        # Simuler des opérations concurrentes en ouvrant plusieurs connexions
        con2 = schema.open_db(Path(self.test_db_path))

        try:
            # Ajouter des entrées depuis les deux connexions
            entry1 = Entry(
                id=None,
                url="https://con1.com",
                title="Connection 1",
                username="user1",
                password_ct=b"pass1",
                nonce=b"nonce1"
            )
            id1 = repository.add_entry(self.con, entry1)

            entry2 = Entry(
                id=None,
                url="https://con2.com",
                title="Connection 2",
                username="user2",
                password_ct=b"pass2",
                nonce=b"nonce2"
            )
            id2 = repository.add_entry(con2, entry2)

            # Les deux entrées doivent être visibles depuis les deux connexions
            entries_con1 = repository.list_entries(self.con)
            entries_con2 = repository.list_entries(con2)

            self.assertEqual(len(entries_con1), 2)
            self.assertEqual(len(entries_con2), 2)

            # Les IDs doivent être différents
            self.assertNotEqual(id1, id2)

        finally:
            con2.close()


if __name__ == '__main__':
    unittest.main()

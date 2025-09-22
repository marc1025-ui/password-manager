#!/usr/bin/env python3

import sys
from pathlib import Path
from os import urandom
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QLineEdit,
                           QTableWidget, QTableWidgetItem, QMessageBox,
                           QDialog, QFormLayout, QSpinBox, QCheckBox, QInputDialog)
from PySide6.QtCore import QTimer, Qt
from core.generator import generate_password
from core.vault import Vault
from crypto.key_derivation import KDFParams
from crypto.keyring import Keyring
from storage import repository
from storage.repository import Entry

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un mot de passe")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.service_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.url_edit = QLineEdit()
        self.notes_edit = QLineEdit()

        layout.addRow("Service:", self.service_edit)
        layout.addRow("Utilisateur:", self.username_edit)
        layout.addRow("Mot de passe:", self.password_edit)
        layout.addRow("URL:", self.url_edit)
        layout.addRow("Notes:", self.notes_edit)

        generate_btn = QPushButton("Générer un mot de passe")
        generate_btn.clicked.connect(self.generate_password)
        layout.addRow(generate_btn)

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Annuler")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        self.setLayout(layout)

    def generate_password(self):
        dialog = GeneratePasswordDialog(self)
        if dialog.exec():
            self.password_edit.setText(dialog.generated_password)

    def get_values(self):
        return {
            'service': self.service_edit.text(),
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'url': self.url_edit.text(),
            'notes': self.notes_edit.text()
        }

class GeneratePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Générer un mot de passe")
        self.generated_password = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(16)

        self.use_upper = QCheckBox("Majuscules")
        self.use_lower = QCheckBox("Minuscules")
        self.use_digits = QCheckBox("Chiffres")
        self.use_special = QCheckBox("Caractères spéciaux")

        self.use_upper.setChecked(True)
        self.use_lower.setChecked(True)
        self.use_digits.setChecked(True)
        self.use_special.setChecked(True)

        form.addRow("Longueur:", self.length_spin)
        form.addRow(self.use_upper)
        form.addRow(self.use_lower)
        form.addRow(self.use_digits)
        form.addRow(self.use_special)

        layout.addLayout(form)

        generate_btn = QPushButton("Générer")
        generate_btn.clicked.connect(self.generate)
        layout.addWidget(generate_btn)

        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        layout.addWidget(self.password_display)

        buttons = QHBoxLayout()
        ok_button = QPushButton("Utiliser ce mot de passe")
        cancel_button = QPushButton("Annuler")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def generate(self):
        self.generated_password = generate_password(
            length=self.length_spin.value(),
            use_upper=self.use_upper.isChecked(),
            use_lower=self.use_lower.isChecked(),
            use_digits=self.use_digits.isChecked(),
            use_specials=self.use_special.isChecked()
        )
        self.password_display.setText(self.generated_password)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionnaire de mots de passe")
        self.setup_ui()
        self.init_vault()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Tableau des mots de passe
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Service", "Utilisateur", "URL", "Actions"])
        layout.addWidget(self.table)

        # Boutons d'action
        button_layout = QHBoxLayout()
        add_button = QPushButton("Ajouter")
        add_button.clicked.connect(self.add_password)
        button_layout.addWidget(add_button)

        layout.addLayout(button_layout)

    def init_vault(self):
        try:
            master_password, ok = QInputDialog.getText(
                self, 'Mot de passe maître',
                'Entrez votre mot de passe maître:',
                QLineEdit.EchoMode.Password
            )
            if ok and master_password:
                self.keyring = Keyring()
                self.vault = Vault(Path("vault.db"))

                # Charger les paramètres KDF existants ou en créer de nouveaux
                meta = repository.load_vault_meta(self.vault.con)
                if meta:
                    # Réutiliser les paramètres existants
                    # Convertir le salt de hex en bytes
                    salt_bytes = bytes.fromhex(meta["salt"].hex())
                    self.kdf_params = KDFParams(
                        salt=salt_bytes,
                        time_cost=meta["kdf_params"]["time_cost"],
                        memory_cost=meta["kdf_params"]["memory_cost"],
                        parallelism=meta["kdf_params"]["parallelism"],
                        hash_len=meta["kdf_params"]["hash_len"]
                    )
                else:
                    # Créer de nouveaux paramètres KDF
                    self.kdf_params = KDFParams(salt=urandom(16))
                    # Sauvegarder les paramètres dans la base
                    repository.save_vault_meta(self.vault.con, {
                        "kdf_name": "argon2",
                        "kdf_params": self.kdf_params.to_dict(),
                        "salt": self.kdf_params.salt,
                        "verifier": b"",  # Non utilisé pour le moment
                        "version": 1
                    })

                self.keyring.unlock(master_password, self.kdf_params)
                self.vault._keyring = self.keyring
                self.refresh_passwords()
            else:
                sys.exit()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            sys.exit(1)

    def refresh_passwords(self):
        self.table.setRowCount(0)
        for entry in self.vault.list_passwords():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.title))
            self.table.setItem(row, 1, QTableWidgetItem(entry.username or ""))
            self.table.setItem(row, 2, QTableWidgetItem(entry.url))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            view_btn = QPushButton("Voir")
            view_btn.clicked.connect(lambda _, id=entry.id: self.view_password(id))
            delete_btn = QPushButton("Supprimer")
            delete_btn.clicked.connect(lambda _, id=entry.id: self.delete_password(id))

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(delete_btn)
            self.table.setCellWidget(row, 3, actions_widget)

    def add_password(self):
        dialog = PasswordDialog(self)
        if dialog.exec():
            values = dialog.get_values()
            try:
                self.vault.add_entry(
                    url=values['url'],
                    title=values['service'],
                    username=values['username'],
                    password=values['password']
                )
                self.refresh_passwords()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def view_password(self, entry_id: int):
        try:
            # Vérifier si le vault est verrouillé
            if not self.vault.is_unlocked():
                # Demander le mot de passe maître
                master_password, ok = QInputDialog.getText(
                    self, 'Vault verrouillé',
                    'Entrez votre mot de passe maître pour déverrouiller le vault:',
                    QLineEdit.EchoMode.Password
                )
                if not ok or not master_password:
                    return

                # Déverrouiller le vault avec les mêmes paramètres KDF
                self.keyring.unlock(master_password, self.kdf_params)
                self.vault._keyring = self.keyring

            # Récupérer et afficher le mot de passe
            entry = self.vault.get_entry(entry_id, reveal=True)
            if entry:
                # Créer un widget personnalisé pour l'affichage temporaire
                dialog = QDialog(self)
                dialog.setWindowTitle("Détails du mot de passe")
                dialog.setModal(True)

                layout = QVBoxLayout()

                text = QLabel(
                    f"Service: {entry.title}\n"
                    f"Utilisateur: {entry.username or ''}\n"
                    f"Mot de passe: {entry.password_ct}\n"
                    f"URL: {entry.url}"
                )
                text.setTextFormat(Qt.PlainText)  # Pour éviter l'interprétation HTML
                layout.addWidget(text)

                timer_label = QLabel("Cette fenêtre se fermera automatiquement dans 10 secondes")
                timer_label.setStyleSheet("color: red")
                layout.addWidget(timer_label)

                dialog.setLayout(layout)
                dialog.show()

                # Créer un timer pour fermer la boîte de dialogue après 10 secondes
                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.timeout.connect(lambda: self.close_and_lock(dialog))
                timer.start(10000)  # 10 secondes

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def close_and_lock(self, dialog):
        """Ferme la boîte de dialogue et verrouille le vault"""
        if dialog and dialog.isVisible():
            dialog.close()
        self.vault.lock()
        QMessageBox.information(self, "Sécurité", "Le vault a été verrouillé pour votre sécurité.")

    def delete_password(self, entry_id: int):
        entry = self.vault.get_entry(entry_id)
        if not entry:
            return

        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer le mot de passe pour {entry.title} ({entry.username}) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.vault.delete(entry_id)
                self.refresh_passwords()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setMinimumSize(800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Qt-based GUI application for the password manager.
Provides a modern dark-themed interface for secure password management
with automatic vault locking and user-friendly dialogs.
"""

import hashlib
import sys
from os import urandom
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.generator import generate_password
from core.vault import Vault
from crypto.key_derivation import KDFParams
from crypto.keyring import Keyring
from storage import repository


def get_vault_path() -> Path:
    """
    Get the appropriate path for the vault database file.
    Uses platform-specific user data directory for better compatibility.
    """
    import platform

    system = platform.system()

    if system == "Darwin":  # macOS
        # Use ~/Library/Application Support/PasswordManager/
        app_support = Path.home() / "Library" / "Application Support" / "PasswordManager"
        app_support.mkdir(parents=True, exist_ok=True)
        return app_support / "vault.db"
    elif system == "Windows":
        # Use %APPDATA%/PasswordManager/
        import os
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        app_dir = appdata / "PasswordManager"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir / "vault.db"
    else:  # Linux and others
        # Use ~/.local/share/passwordmanager/
        data_home = Path.home() / ".local" / "share" / "passwordmanager"
        data_home.mkdir(parents=True, exist_ok=True)
        return data_home / "vault.db"


class SignUpDialog(QDialog):
    """
    Dialog for first-time user registration.
    Handles master password creation with validation and confirmation.
    """

    def __init__(self, parent=None):
        """Initialize the signup dialog."""
        super().__init__(parent)
        self.setWindowTitle("Première inscription - Créer votre mot de passe maître")
        self.setMinimumWidth(400)
        f = QFormLayout(self)

        # Ajouter un texte d'explication
        welcome_label = QLabel("Bienvenue ! Créez votre mot de passe maître pour sécuriser vos données.")
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("color: #94a3b8; margin-bottom: 10px;")
        f.addRow(welcome_label)

        # Input fields
        self.username = QLineEdit()
        self.pw1 = QLineEdit()
        self.pw1.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw2 = QLineEdit()
        self.pw2.setEchoMode(QLineEdit.EchoMode.Password)

        # Ajouter des conseils pour le mot de passe
        password_hint = QLabel("Le mot de passe doit contenir au moins 8 caractères.")
        password_hint.setStyleSheet("color: #94a3b8; font-size: 11px;")

        f.addRow("Nom d'utilisateur :", self.username)
        f.addRow("Mot de passe maître :", self.pw1)
        f.addRow("Confirmer le mot de passe :", self.pw2)
        f.addRow(password_hint)

        # Buttons
        btns = QHBoxLayout()
        ok = QPushButton("Créer mon compte")
        cancel = QPushButton("Annuler")
        ok.clicked.connect(self.validate_and_accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        f.addRow(btns)

    def validate_and_accept(self):
        """Validate form inputs and accept if valid."""
        username, pw1, pw2 = self.values()

        # Validation du nom d'utilisateur
        if not username:
            QMessageBox.warning(self, "Erreur", "Le nom d'utilisateur ne peut pas être vide.")
            return

        # Validation du mot de passe
        if not pw1:
            QMessageBox.warning(self, "Erreur", "Le mot de passe maître ne peut pas être vide.")
            return

        MIN_PASSWORD_LENGTH = 8
        if len(pw1) < MIN_PASSWORD_LENGTH:
            QMessageBox.warning(self, "Erreur", "Le mot de passe doit contenir au moins 8 caractères.")
            return

        if pw1 != pw2:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return

        # Confirmation finale
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Créer le compte pour '{username}' ?\n\nATTENTION: Si vous oubliez ce mot de passe maître, vous perdrez définitivement l'accès à tous vos mots de passe !",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def values(self):
        """Get form values."""
        return self.username.text().strip(), self.pw1.text(), self.pw2.text()


class LoginDialog(QDialog):
    """
    Dialog for user authentication.
    Handles master password entry for existing vaults.
    """

    def __init__(self, expected_username: str, parent=None):
        """
        Initialize the login dialog.

        Args:
            expected_username: Username to pre-fill (can be empty)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Connexion - Entrez votre mot de passe maître")
        self.setMinimumWidth(350)
        f = QFormLayout(self)

        # Message d'accueil
        welcome_label = QLabel("Entrez vos identifiants pour accéder à votre coffre-fort.")
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("color: #94a3b8; margin-bottom: 10px;")
        f.addRow(welcome_label)

        # Input fields
        self.username = QLineEdit()
        self.username.setText(expected_username or "")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        f.addRow("Nom d'utilisateur :", self.username)
        f.addRow("Mot de passe maître :", self.password)

        # Buttons
        btns = QHBoxLayout()
        ok = QPushButton("Se connecter")
        cancel = QPushButton("Annuler")
        ok.clicked.connect(self.validate_and_accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        f.addRow(btns)

    def validate_and_accept(self):
        """Validate login inputs and accept if valid."""
        username, password = self.values()

        if not username:
            QMessageBox.warning(self, "Erreur", "Le nom d'utilisateur ne peut pas être vide.")
            return

        if not password:
            QMessageBox.warning(self, "Erreur", "Le mot de passe ne peut pas être vide.")
            return

        self.accept()

    def values(self):
        """Get login credentials."""
        return self.username.text().strip(), self.password.text()


class PasswordDialog(QDialog):
    """
    Dialog for adding new password entries.
    Provides form fields for service details and password generation.
    """

    def __init__(self, parent=None):
        """Initialize the password entry dialog."""
        super().__init__(parent)
        self.setWindowTitle("Ajouter un mot de passe")
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog user interface."""
        layout = QFormLayout()

        # Input fields for password entry
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

        # Password generation button
        generate_btn = QPushButton("Générer un mot de passe")
        generate_btn.clicked.connect(self.generate_password)
        layout.addRow(generate_btn)

        # Action buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Annuler")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)
        self.setLayout(layout)
        self.setContentsMargins(14, 14, 14, 14)
        self.layout().setSpacing(10)

    def generate_password(self):
        """Open password generator dialog and use result."""
        dialog = GeneratePasswordDialog(self)
        if dialog.exec():
            self.password_edit.setText(dialog.generated_password)

    def get_values(self):
        """Get all form values as dictionary."""
        return {
            'service': self.service_edit.text(),
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'url': self.url_edit.text(),
            'notes': self.notes_edit.text()
        }


class GeneratePasswordDialog(QDialog):
    """
    Dialog for generating strong passwords with customizable parameters.
    Allows users to specify length and character types for password generation.
    """

    def __init__(self, parent=None):
        """Initialize the password generator dialog."""
        super().__init__(parent)
        self.setWindowTitle("Générer un mot de passe")
        self.generated_password = ""
        self.setup_ui()

    def setup_ui(self):
        """Set up the password generator interface."""
        layout = QVBoxLayout()

        # Password generation parameters
        form = QFormLayout()
        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 64)
        self.length_spin.setValue(16)

        # Character type checkboxes
        self.use_upper = QCheckBox("Majuscules")
        self.use_lower = QCheckBox("Minuscules")
        self.use_digits = QCheckBox("Chiffres")
        self.use_special = QCheckBox("Caractères spéciaux")

        # Set default selections (all enabled)
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

        # Generate button
        generate_btn = QPushButton("Générer")
        generate_btn.clicked.connect(self.generate)
        layout.addWidget(generate_btn)

        # Password display
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        layout.addWidget(self.password_display)

        # Action buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("Utiliser ce mot de passe")
        cancel_button = QPushButton("Annuler")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        self.setLayout(layout)
        self.setContentsMargins(14, 14, 14, 14)
        self.layout().setSpacing(10)

    def generate(self):
        """Generate a new password with current parameters."""
        self.generated_password = generate_password(
            length=self.length_spin.value(),
            use_upper=self.use_upper.isChecked(),
            use_lower=self.use_lower.isChecked(),
            use_digits=self.use_digits.isChecked(),
            use_specials=self.use_special.isChecked()
        )

        self.password_display.setText(self.generated_password)


class MainWindow(QMainWindow):
    """
    Main application window for the password manager.
    Provides the primary interface for password management operations.
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("Gestionnaire de mots de passe")
        self.setup_ui()
        self.init_vault()

    def setup_ui(self):
        """Set up the main window user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Barre de recherche
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Rechercher par service / utilisateur / URL…")
        search_row.addWidget(QLabel("Recherche :"))
        search_row.addWidget(self.search_edit)
        layout.addLayout(search_row)
        self.search_edit.textChanged.connect(self.refresh_passwords)

        # Tableau des mots de passe
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Service", "Utilisateur", "URL", "Actions"])
        layout.addWidget(self.table)

        # Configure table appearance
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)

        # Set column widths
        self.table.setColumnWidth(0, 140)  # Service
        self.table.setColumnWidth(1, 100)  # Utilisateur
        self.table.setColumnWidth(2, 100)  # URL

        # Action buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Ajouter")
        add_button.clicked.connect(self.add_password)
        button_layout.addWidget(add_button)

        layout.addLayout(button_layout)

    def init_vault(self):
        """
        Initialize the vault on application startup.
        Handles both new vault creation and existing vault login.
        """

        try:
            # Utiliser le chemin approprié pour la base de données selon la plateforme
            vault_path = get_vault_path()

            # Créer le vault pour pouvoir charger les métadonnées
            self.vault = Vault(vault_path)
            meta = repository.load_vault_meta(self.vault.con)
            is_new_vault = meta is None

            if is_new_vault:
                # Première utilisation : création du compte
                signup_dialog = SignUpDialog(self)
                if not signup_dialog.exec():
                    sys.exit()
                username, pw1, pw2 = signup_dialog.values()

                # La validation est déjà faite dans SignUpDialog.validate_and_accept()
                # mais on garde une vérification de sécurité
                if not pw1 or pw1 != pw2:
                    QMessageBox.critical(self, "Erreur", "Erreur lors de la création du compte.")
                    sys.exit(1)

                # Initialiser le vault avec le mot de passe maître
                self.keyring = Keyring()
                self.vault.init_master_password(pw1)
                self.kdf_params = KDFParams(salt=urandom(16))

                # Dériver la clé et créer un verifier
                from crypto.key_derivation import derive_key
                key, _ = derive_key(pw1, self.kdf_params)
                verifier = hashlib.sha256(key).digest()

                # Stocker les métadonnées du vault
                vault_meta_to_save = {
                    "kdf_name": "argon2",
                    "kdf_params": self.kdf_params.to_dict(),
                    "salt": self.kdf_params.salt.hex(),  # Convertir en hex pour la sauvegarde
                    "verifier": verifier,
                    "version": 1
                }
                repository.save_vault_meta(self.vault.con, vault_meta_to_save)

                # Déverrouiller le keyring avec l'objet KDFParams directement
                vault_meta_for_unlock = {
                    "kdf_params": self.kdf_params,  # Passer directement l'objet KDFParams
                    "verifier": verifier
                }

                self.keyring.unlock(pw1, vault_meta_for_unlock)
                self.vault._keyring = self.keyring

                # Afficher un message de succès
                QMessageBox.information(self, "Succès", f"Compte créé avec succès pour {username} !")
                self.refresh_passwords()
            else:
                # Vault existant : demander le mot de passe maître
                login_dialog = LoginDialog("", self)
                attempts = 0
                max_attempts = 3

                while attempts < max_attempts:
                    if not login_dialog.exec():
                        sys.exit()
                    username, master_password = login_dialog.values()

                    # La validation est déjà faite dans LoginDialog.validate_and_accept()
                    try:
                        # Tenter de déverrouiller avec le mot de passe
                        self.keyring = Keyring()
                        self.keyring.unlock(master_password, meta)
                        self.vault._keyring = self.keyring
                        self.refresh_passwords()
                        return
                    except ValueError:
                        # Mot de passe incorrect
                        attempts += 1
                        if attempts >= max_attempts:
                            QMessageBox.critical(self, "Erreur", "Nombre maximum de tentatives atteint.")
                            sys.exit(1)
                        else:
                            QMessageBox.warning(self, "Erreur", "Mot de passe incorrect.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'initialisation: {str(e)}")
            sys.exit(1)

    def refresh_passwords(self):
        """
        Refresh the password table with current entries.
        Applies search filter if active.
        """
        query = (self.search_edit.text() if hasattr(self, "search_edit") else "") or ""
        self.table.setRowCount(0)

        # Récupération des entrées (privilégier Vault.search si dispo)
        try:
            if query.strip() and hasattr(self.vault, "search"):
                entries = self.vault.search(query.strip())
            else:
                entries = self.vault.list_passwords()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return

        # Populate table with entries
        for entry in entries:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.title or ""))  # Service
            self.table.setItem(row, 1, QTableWidgetItem(entry.username or ""))  # Utilisateur
            self.table.setItem(row, 2, QTableWidgetItem(entry.url or ""))  # URL

            # Create action buttons widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            view_btn = QPushButton("Voir")
            view_btn.clicked.connect(lambda _, id=entry.id: self.view_password(id))
            delete_btn = QPushButton("Supprimer")
            delete_btn.clicked.connect(lambda _, id=entry.id: self.delete_password(id))
            actions_layout.setSpacing(6)
            for b in (view_btn, delete_btn):
                b.setMinimumWidth(128)
            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 3, actions_widget)

    def add_password(self):
        """
        Handle adding a new password entry.
        Automatically unlocks vault if needed and re-locks for security.
        """
        dialog = PasswordDialog(self)
        if dialog.exec():
            values = dialog.get_values()
            try:
                # Ajouter l'entrée (avec déverrouillage automatique si nécessaire)
                self.vault.add_entry(
                    url=values['url'],
                    title=values['service'],
                    username=values['username'],
                    password=values['password']
                )
                self.refresh_passwords()
                QMessageBox.information(self, "Succès", "Mot de passe ajouté avec succès !")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def view_password(self, entry_id: int):
        """
        View a password entry with temporary display.

        Args:
            entry_id: ID of the entry to view
        """
        try:
            # Vérifier si le vault est verrouillé
            if not self.vault.is_unlocked():
                attempts = 0
                max_attempts = 3

                while attempts < max_attempts:
                    # Demander le mot de passe maître
                    master_password, ok = QInputDialog.getText(
                        self, 'Vault verrouillé',
                        f'Entrez votre mot de passe maître pour déverrouiller le vault:\n{max_attempts - attempts} tentatives restantes',
                        QLineEdit.EchoMode.Password
                    )

                    if not ok:  # L'utilisateur a appuyé sur Annuler
                        return

                    if not master_password:  # Champ vide
                        QMessageBox.warning(self, "Erreur", "Le mot de passe ne peut pas être vide.")
                        attempts += 1
                        if attempts >= max_attempts:
                            QMessageBox.critical(self, "Erreur", "Nombre maximum de tentatives atteint.")
                            return
                        continue

                    try:
                        # Charger les métadonnées du vault et tenter de déverrouiller
                        meta = repository.load_vault_meta(self.vault.con)
                        self.keyring.unlock(master_password, meta)
                        self.vault._keyring = self.keyring
                        break  # Sort de la boucle si le déverrouillage réussit
                    except ValueError:
                        # Mot de passe incorrect
                        attempts += 1
                        if attempts >= max_attempts:
                            QMessageBox.critical(self, "Erreur", "Nombre maximum de tentatives atteint.")
                            return
                        else:
                            QMessageBox.warning(self, "Erreur", "Mot de passe incorrect.")
                            continue

            # Si on arrive ici, le vault est déverrouillé
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
                text.setTextFormat(Qt.PlainText)
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
        """
        Close dialog and lock vault for security.

        Args:
            dialog: The dialog to close
        """
        if dialog and dialog.isVisible():
            dialog.close()
        self.vault.lock()
        QMessageBox.information(self, "Sécurité", "Le vault a été verrouillé pour votre sécurité.")

    def delete_password(self, entry_id: int):
        """
        Delete a password entry with confirmation.

        Args:
            entry_id: ID of the entry to delete
        """
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


def load_qss() -> str:
    """
    Load the application's dark theme CSS stylesheet.

    Returns:
        CSS stylesheet string for dark theme UI
    """
    return """
    /* --- Base --- */
    * { font-family: "Inter", "SF Pro Text", "Segoe UI", "Roboto", "Helvetica Neue", Arial; }
    QWidget { background: #0f172a; color: #e2e8f0; }                 /* gris ardoise (dark) */
    QMainWindow { background: #0f172a; }

    /* --- Champs & Boutons --- */
    QLineEdit, QSpinBox, QComboBox {
        background: #111827; border: 1px solid #1f2937; border-radius: 10px;
        padding: 8px 10px; selection-background-color: #2563eb;
    }
    QPushButton {
        background: #1f2937; border: 1px solid #334155; border-radius: 12px;
        padding: 8px 14px; font-weight: 600;
    }
    QPushButton:hover { background: #374151; }
    QPushButton:pressed { background: #111827; }

    /* --- Labels secondaires --- */
    QLabel[muted="true"] { color: #94a3b8; }

    /* --- Table --- */
    QTableWidget {
        background: #0b1220; border: 1px solid #1f2937; border-radius: 12px;
        gridline-color: #1f2937; alternate-background-color: #0e172b;
    }
    QHeaderView::section {
        background: #0b1220; color: #cbd5e1; border: none; padding: 8px 10px;
        border-right: 1px solid #1f2937; font-weight: 600;
    }
    QHeaderView::section:last { border-right: none; }
    QTableWidget::item:selected { background: #1d4ed8; color: #f8fafc; }
    QTableCornerButton::section { background: #0b1220; border: none; }

    /* --- Dialogs --- */
    QDialog {
        background: #0b1220; border: 1px solid #1f2937; border-radius: 16px;
    }

    /* --- Scrollbars --- */
    QScrollBar:vertical {
        background: transparent; width: 10px; margin: 10px 2px 10px 0;
    }
    QScrollBar::handle:vertical {
        background: #334155; border-radius: 5px; min-height: 30px;
    }
    QScrollBar::handle:vertical:hover { background: #475569; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

    /* --- Inputs "focus" --- */
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, .15);
    }
    """


def main():
    """
    Main application entry point.
    Sets up Qt application with dark theme and shows main window.
    """
    app = QApplication(sys.argv)
    app.setFont(QFont("Inter", 11))
    app.setStyleSheet(load_qss())
    window = MainWindow()
    window.setMinimumSize(800, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

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


class SignUpDialog(QDialog):
    """
    Dialog for first-time user registration.
    Handles master password creation with validation and confirmation.
    """

    def __init__(self, parent=None):
        """Initialize the signup dialog."""
        super().__init__(parent)
        self.setWindowTitle("First Registration - Create Your Master Password")
        self.setMinimumWidth(400)
        f = QFormLayout(self)

        # Add explanatory text
        welcome_label = QLabel(
            "Welcome! Create your master password to secure your data."
        )
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("color: #94a3b8; margin-bottom: 10px;")
        f.addRow(welcome_label)

        # Input fields
        self.username = QLineEdit()
        self.pw1 = QLineEdit()
        self.pw1.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw2 = QLineEdit()
        self.pw2.setEchoMode(QLineEdit.EchoMode.Password)

        # Add password guidelines
        password_hint = QLabel("Password must contain at least 8 characters.")
        password_hint.setStyleSheet("color: #94a3b8; font-size: 11px;")

        f.addRow("Username:", self.username)
        f.addRow("Master Password:", self.pw1)
        f.addRow("Confirm Password:", self.pw2)
        f.addRow(password_hint)

        # Buttons
        btns = QHBoxLayout()
        ok = QPushButton("Create Account")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self.validate_and_accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        f.addRow(btns)

    def validate_and_accept(self):
        """Validate form inputs and accept if valid."""
        username, pw1, pw2 = self.values()

        # Username validation
        if not username:
            QMessageBox.warning(
                self, "Error", "Username cannot be empty."
            )
            return

        # Password validation
        if not pw1:
            QMessageBox.warning(
                self, "Error", "Master password cannot be empty."
            )
            return

        MIN_PASSWORD_LENGTH = 8
        if len(pw1) < MIN_PASSWORD_LENGTH:
            QMessageBox.warning(
                self,
                "Error",
                f"Password must contain at least {MIN_PASSWORD_LENGTH} characters.",
            )
            return

        if pw1 != pw2:
            QMessageBox.warning(
                self, "Error", "Passwords do not match."
            )
            return

        # Final confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Create account for '{username}'?\n\n"
            "WARNING: If you forget this master password, you will "
            "permanently lose access to all your passwords!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
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
        self.setWindowTitle("Login - Enter Your Master Password")
        self.setMinimumWidth(350)
        f = QFormLayout(self)

        # Welcome message
        welcome_label = QLabel(
            "Enter your credentials to access your vault."
        )
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("color: #94a3b8; margin-bottom: 10px;")
        f.addRow(welcome_label)

        # Input fields
        self.username = QLineEdit()
        self.username.setText(expected_username or "")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        f.addRow("Username:", self.username)
        f.addRow("Master Password:", self.password)

        # Buttons
        btns = QHBoxLayout()
        ok = QPushButton("Login")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self.validate_and_accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        f.addRow(btns)

    def validate_and_accept(self):
        """Validate login inputs and accept if valid."""
        username, password = self.values()

        if not username:
            QMessageBox.warning(
                self, "Error", "Username cannot be empty."
            )
            return

        if not password:
            QMessageBox.warning(
                self, "Error", "Password cannot be empty."
            )
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
        self.setWindowTitle("Add Password")
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
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Password:", self.password_edit)
        layout.addRow("URL:", self.url_edit)
        layout.addRow("Notes:", self.notes_edit)

        # Password generation button
        generate_btn = QPushButton("Generate Password")
        generate_btn.clicked.connect(self.generate_password)
        layout.addRow(generate_btn)

        # Action buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
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
            "service": self.service_edit.text(),
            "username": self.username_edit.text(),
            "password": self.password_edit.text(),
            "url": self.url_edit.text(),
            "notes": self.notes_edit.text(),
        }


class GeneratePasswordDialog(QDialog):
    """
    Dialog for generating strong passwords with customizable parameters.
    Allows users to specify length and character types for password generation.
    """

    def __init__(self, parent=None):
        """Initialize the password generator dialog."""
        super().__init__(parent)
        self.setWindowTitle("Generate Password")
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
        self.use_upper = QCheckBox("Uppercase Letters")
        self.use_lower = QCheckBox("Lowercase Letters")
        self.use_digits = QCheckBox("Digits")
        self.use_special = QCheckBox("Special Characters")

        # Set default selections (all enabled)
        self.use_upper.setChecked(True)
        self.use_lower.setChecked(True)
        self.use_digits.setChecked(True)
        self.use_special.setChecked(True)

        form.addRow("Length:", self.length_spin)
        form.addRow(self.use_upper)
        form.addRow(self.use_lower)
        form.addRow(self.use_digits)
        form.addRow(self.use_special)

        layout.addLayout(form)

        # Generate button
        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self.generate)
        layout.addWidget(generate_btn)

        # Password display
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        layout.addWidget(self.password_display)

        # Action buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("Use This Password")
        cancel_button = QPushButton("Cancel")
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
            use_specials=self.use_special.isChecked(),
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
        self.setWindowTitle("Password Manager")
        self.setup_ui()
        self.init_vault()

    def setup_ui(self):
        """Set up the main window user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Search bar
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search by service / username / URL…"
        )
        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self.search_edit)
        layout.addLayout(search_row)
        self.search_edit.textChanged.connect(self.refresh_passwords)

        # Password table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Service", "Username", "URL", "Actions"]
        )
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
        self.table.setColumnWidth(1, 100)  # Username
        self.table.setColumnWidth(2, 100)  # URL

        # Action buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_password)
        button_layout.addWidget(add_button)

        layout.addLayout(button_layout)

    def init_vault(self):
        """
        Initialize the vault on application startup.
        Handles both new vault creation and existing vault login.
        """
        try:
            # Check if vault exists and contains metadata
            vault_path = Path("vault.db")

            # Create vault to load metadata
            self.vault = Vault(vault_path)
            meta = repository.load_vault_meta(self.vault.con)
            is_new_vault = meta is None

            if is_new_vault:
                # First use: account creation
                signup_dialog = SignUpDialog(self)
                if not signup_dialog.exec():
                    sys.exit()
                username, pw1, pw2 = signup_dialog.values()

                # Validation is already done in SignUpDialog.validate_and_accept()
                # but keep security check
                if not pw1 or pw1 != pw2:
                    QMessageBox.critical(
                        self, "Error", "Error creating account."
                    )
                    sys.exit(1)

                # Initialize vault with master password
                self.keyring = Keyring()
                self.vault.init_master_password(pw1)
                self.kdf_params = KDFParams(salt=urandom(16))

                # Derive key and create verifier
                from crypto.key_derivation import derive_key

                key, _ = derive_key(pw1, self.kdf_params)
                verifier = hashlib.sha256(key).digest()

                # Store vault metadata
                vault_meta_to_save = {
                    "kdf_name": "argon2",
                    "kdf_params": self.kdf_params.to_dict(),
                    "salt": self.kdf_params.salt.hex(),  # Convert to hex for storage
                    "verifier": verifier,
                    "version": 1,
                }
                repository.save_vault_meta(self.vault.con, vault_meta_to_save)

                # Unlock keyring with KDFParams object directly
                vault_meta_for_unlock = {
                    "kdf_params": self.kdf_params,  # Pass KDFParams object directly
                    "verifier": verifier,
                }

                self.keyring.unlock(pw1, vault_meta_for_unlock)
                self.vault._keyring = self.keyring

                # Show success message
                QMessageBox.information(
                    self, "Success", f"Account created successfully for {username}!"
                )
                self.refresh_passwords()
            else:
                # Existing vault: request master password
                login_dialog = LoginDialog("", self)
                attempts = 0
                max_attempts = 3

                while attempts < max_attempts:
                    if not login_dialog.exec():
                        sys.exit()
                    username, master_password = login_dialog.values()

                    # Validation is already done in LoginDialog.validate_and_accept()
                    try:
                        # Attempt to unlock with password
                        self.keyring = Keyring()
                        self.keyring.unlock(master_password, meta)
                        self.vault._keyring = self.keyring
                        self.refresh_passwords()
                        return
                    except ValueError:
                        # Incorrect password
                        attempts += 1
                        if attempts >= max_attempts:
                            QMessageBox.critical(
                                self, "Error", "Maximum attempts reached."
                            )
                            sys.exit(1)
                        else:
                            QMessageBox.warning(
                                self, "Error", "Incorrect password."
                            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Initialization error: {e!s}"
            )
            sys.exit(1)

    def refresh_passwords(self):
        """
        Refresh the password table with current entries.
        Applies search filter if active.
        """
        query = (self.search_edit.text() if hasattr(self, "search_edit") else "") or ""
        self.table.setRowCount(0)

        # Retrieve entries (prefer Vault.search if available)
        try:
            if query.strip() and hasattr(self.vault, "search"):
                entries = self.vault.search(query.strip())
            else:
                entries = self.vault.list_passwords()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        # Populate table with entries
        for entry in entries:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.title or ""))  # Service
            self.table.setItem(
                row, 1, QTableWidgetItem(entry.username or "")
            )  # Username
            self.table.setItem(row, 2, QTableWidgetItem(entry.url or ""))  # URL

            # Create action buttons widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            view_btn = QPushButton("View")
            delete_btn = QPushButton("Delete")

            # Avoid shadowing builtin 'id' by using closures
            def make_view_handler(entry_id):
                return lambda _: self.view_password(entry_id)

            def make_delete_handler(entry_id):
                return lambda _: self.delete_password(entry_id)

            view_btn.clicked.connect(make_view_handler(entry.id))
            delete_btn.clicked.connect(make_delete_handler(entry.id))

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
                # Check if vault is unlocked
                master_password = None
                if not self.vault.is_unlocked():
                    # Request master password to unlock temporarily
                    master_password, ok = QInputDialog.getText(
                        self,
                        "Vault Locked",
                        "Enter your master password to add this entry:",
                        QLineEdit.EchoMode.Password,
                    )
                    if not ok or not master_password:
                        return  # User cancelled

                # Add entry (with automatic unlocking if needed)
                self.vault.add_entry(
                    url=values["url"],
                    title=values["service"],
                    username=values["username"],
                    password=values["password"],
                    master_password=master_password,  # Pass master password if needed
                )
                self.refresh_passwords()
                QMessageBox.information(
                    self, "Success", "Password added successfully!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def view_password(self, entry_id: int):
        """
        View a password entry with temporary display.

        Args:
            entry_id: ID of the entry to view
        """
        try:
            # Check if vault is locked
            if not self.vault.is_unlocked():
                attempts = 0
                max_attempts = 3

                while attempts < max_attempts:
                    # Request master password
                    master_password, ok = QInputDialog.getText(
                        self,
                        "Vault Locked",
                        f"Enter your master password to unlock vault:\n{max_attempts - attempts} attempts remaining",
                        QLineEdit.EchoMode.Password,
                    )

                    if not ok:  # User pressed Cancel
                        return

                    if not master_password:  # Empty field
                        QMessageBox.warning(
                            self, "Error", "Password cannot be empty."
                        )
                        attempts += 1
                        if attempts >= max_attempts:
                            QMessageBox.critical(
                                self, "Error", "Maximum attempts reached."
                            )
                            return
                        continue

                    try:
                        # Load vault metadata and attempt to unlock
                        meta = repository.load_vault_meta(self.vault.con)
                        self.keyring.unlock(master_password, meta)
                        self.vault._keyring = self.keyring
                        break  # Exit loop if unlock succeeds
                    except ValueError:
                        # Incorrect password
                        attempts += 1
                        if attempts >= max_attempts:
                            QMessageBox.critical(
                                self, "Error", "Maximum attempts reached."
                            )
                            return
                        QMessageBox.warning(
                            self, "Error", "Incorrect password."
                        )
                        continue

            # If we get here, vault is unlocked
            # Retrieve and display password
            entry = self.vault.get_entry(entry_id, reveal=True)
            if entry:
                # Create custom widget for temporary display
                dialog = QDialog(self)
                dialog.setWindowTitle("Password Details")
                dialog.setModal(True)

                layout = QVBoxLayout()

                text = QLabel(
                    f"Service: {entry.title}\n"
                    f"Username: {entry.username or ''}\n"
                    f"Password: {entry.password_ct}\n"
                    f"URL: {entry.url}"
                )
                text.setTextFormat(Qt.PlainText)
                layout.addWidget(text)

                timer_label = QLabel(
                    "This window will close automatically in 10 seconds"
                )
                timer_label.setStyleSheet("color: red")
                layout.addWidget(timer_label)

                dialog.setLayout(layout)
                dialog.show()

                # Create timer to close dialog after 10 seconds
                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.timeout.connect(lambda: self.close_and_lock(dialog))
                timer.start(10000)  # 10 seconds

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def close_and_lock(self, dialog):
        """
        Close dialog and lock vault for security.

        Args:
            dialog: The dialog to close
        """
        if dialog and dialog.isVisible():
            dialog.close()
        self.vault.lock()
        QMessageBox.information(
            self, "Security", "Vault has been locked for your security."
        )

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
            f"Do you really want to delete the password for {entry.title} ({entry.username})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.vault.delete(entry_id)
                self.refresh_passwords()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


def load_qss() -> str:
    """
    Load the application's dark theme CSS stylesheet.

    Returns:
        CSS stylesheet string for dark theme UI
    """
    return """
    /* --- Base --- */
    * { font-family: "Inter", "SF Pro Text", "Segoe UI", "Roboto", "Helvetica Neue", Arial; }
    QWidget { background: #0f172a; color: #e2e8f0; }                 /* dark slate theme */
    QMainWindow { background: #0f172a; }

    /* --- Input Fields & Buttons --- */
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

    /* --- Secondary Labels --- */
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

    /* --- Input Focus --- */
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

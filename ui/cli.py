#!/usr/bin/env python3
"""
Command Line Interface for the password manager.
Provides terminal-based access to vault operations with
comprehensive argument parsing and secure password handling.
"""

import argparse
import getpass
import sys
from pathlib import Path

from core.vault import Vault


def main():
    """
    Main CLI entry point.
    Parses command line arguments and routes to appropriate handlers.
    """
    parser = argparse.ArgumentParser(
        description="Secure Password Manager - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add --url https://example.com --username john
  %(prog)s list
  %(prog)s search google
  %(prog)s view 1
  %(prog)s delete 5
        """,
    )

    # Global options
    parser.add_argument(
        "--vault",
        type=Path,
        default=Path("vault.db"),
        help="Path to vault database file (default: vault.db)",
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command to add a new password
    add_cmd = subparsers.add_parser("add", help="Add a new password entry")
    add_cmd.add_argument("--url", required=True, help="Service URL")
    add_cmd.add_argument("--title", help="Service title (defaults to URL)")
    add_cmd.add_argument("--username", help="Username for the service")
    add_cmd.add_argument(
        "--generate", "-g", action="store_true", help="Generate random password"
    )
    add_cmd.add_argument("--length", type=int, default=16, help="Password length")

    # Command to list all passwords
    subparsers.add_parser("list", help="List all services")

    # Command to delete a password
    del_cmd = subparsers.add_parser("delete", help="Delete a password entry")
    del_cmd.add_argument("id", type=int, help="Entry ID to delete")

    # Command to search passwords
    search_cmd = subparsers.add_parser("search", help="Search password entries")
    search_cmd.add_argument("query", help="Search query")

    # Command to view a specific password
    view_cmd = subparsers.add_parser("view", help="View password details")
    view_cmd.add_argument("id", type=int, help="Entry ID to view")

    # Command to generate a password (without storing)
    gen_cmd = subparsers.add_parser("generate", help="Generate a password")
    gen_cmd.add_argument("--length", type=int, default=16, help="Password length")
    gen_cmd.add_argument(
        "--no-upper", action="store_true", help="Exclude uppercase letters"
    )
    gen_cmd.add_argument(
        "--no-lower", action="store_true", help="Exclude lowercase letters"
    )
    gen_cmd.add_argument("--no-digits", action="store_true", help="Exclude digits")
    gen_cmd.add_argument(
        "--no-special", action="store_true", help="Exclude special characters"
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Handle different commands
    try:
        if args.command == "generate":
            handle_generate(args)
        else:
            # Commands that require vault access
            vault = Vault(args.vault)

            # Check if vault is initialized
            from storage import repository

            meta = repository.load_vault_meta(vault.con)

            if not meta and args.command != "init":
                print(
                    "❌ Vault not initialized. Please run the GUI first to set up your master password."
                )
                sys.exit(1)

            # Unlock vault for operations that need it
            if args.command in ["add", "view"]:
                master_password = getpass.getpass("Enter master password: ")
                vault.unlock(master_password)

            # Route to command handlers
            if args.command == "add":
                handle_add(vault, args)
            elif args.command == "list":
                handle_list(vault)
            elif args.command == "search":
                handle_search(vault, args)
            elif args.command == "view":
                handle_view(vault, args)
            elif args.command == "delete":
                handle_delete(vault, args)

    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def handle_generate(args):
    """
    Handle password generation command.

    Args:
        args: Parsed command line arguments
    """
    from core.generator import generate_password

    # Generate password with specified parameters
    password = generate_password(
        length=args.length,
        use_upper=not args.no_upper,
        use_lower=not args.no_lower,
        use_digits=not args.no_digits,
        use_specials=not args.no_special,
    )

    print(f"Generated password: {password}")


def handle_add(vault, args):
    """
    Handle adding a new password entry.

    Args:
        vault: Vault instance (must be unlocked)
        args: Parsed command line arguments
    """
    from core.generator import generate_password

    # Get password (generate or prompt)
    if args.generate:
        password = generate_password(length=args.length)
        print(f"Generated password: {password}")
    else:
        password = getpass.getpass("Enter password to store: ")

    # Add entry to vault
    entry_id = vault.add_entry(
        url=args.url,
        title=args.title,
        username=args.username,
        password=password,
    )

    print(f"✅ Password entry added with ID: {entry_id}")


def handle_list(vault):
    """
    Handle listing all password entries.

    Args:
        vault: Vault instance
    """
    entries = vault.list_passwords()

    if not entries:
        print("📭 No password entries found.")
        return

    print(f"📋 Found {len(entries)} password entries:")
    print("-" * 60)

    for entry in entries:
        title = entry.title or "Untitled"
        username = entry.username or "No username"
        print(f"[{entry.id}] {title}")
        print(f"    Username: {username}")
        print(f"    URL: {entry.url}")
        print()


def handle_search(vault, args):
    """
    Handle searching password entries.

    Args:
        vault: Vault instance
        args: Parsed command line arguments containing search query
    """
    results = list(vault.search(args.query))

    if not results:
        print(f"🔍 No entries found matching '{args.query}'")
        return

    print(f"🔍 Found {len(results)} entries matching '{args.query}':")
    print("-" * 60)

    for entry in results:
        title = entry.title or "Untitled"
        username = entry.username or "No username"
        print(f"[{entry.id}] {title}")
        print(f"    Username: {username}")
        print(f"    URL: {entry.url}")
        print()


def handle_view(vault, args):
    """
    Handle viewing a specific password entry.

    Args:
        vault: Vault instance (must be unlocked)
        args: Parsed command line arguments containing entry ID
    """
    entry = vault.get_entry(args.id, reveal=True)

    if not entry:
        print(f"❌ Entry with ID {args.id} not found.")
        return

    print("🔍 Password Entry Details:")
    print("-" * 40)
    print(f"ID: {entry.id}")
    print(f"Service: {entry.title or 'Untitled'}")
    print(f"Username: {entry.username or 'None'}")
    print(f"URL: {entry.url}")
    print(f"Password: {entry.password_ct}")
    print("-" * 40)
    print("⚠️ Password displayed above. Remember to clear your terminal!")


def handle_delete(vault, args):
    """
    Handle deleting a password entry.

    Args:
        vault: Vault instance
        args: Parsed command line arguments containing entry ID
    """
    # Get entry details for confirmation
    entry = vault.get_entry(args.id)
    if not entry:
        print(f"❌ Entry with ID {args.id} not found.")
        return

    # Confirm deletion
    title = entry.title or "Untitled"
    username = entry.username or "No username"

    confirm = input(
        f"⚠️ Delete password for '{title}' ({username})? [y/N]: "
    ).lower().strip()

    if confirm not in ["y", "yes"]:
        print("🚫 Deletion cancelled.")
        return

    # Perform deletion
    if vault.delete(args.id):
        print(f"✅ Entry '{title}' deleted successfully.")
    else:
        print(f"❌ Failed to delete entry with ID {args.id}.")


if __name__ == "__main__":
    main()

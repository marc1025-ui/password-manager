#!/usr/bin/env python3

import argparse
import sys
from getpass import getpass
from pathlib import Path

from core.generator import generate_password
from core.vault import Vault
from crypto.keyring import Keyring


def create_parser():
    parser = argparse.ArgumentParser(
        description="Gestionnaire de mots de passe sécurisé"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # Commande pour générer un mot de passe
    gen = subparsers.add_parser("generate", help="Générer un nouveau mot de passe")
    gen.add_argument(
        "-l", "--length", type=int, default=16, help="Longueur du mot de passe"
    )
    gen.add_argument("--no-digits", action="store_true", help="Sans chiffres")
    gen.add_argument(
        "--no-special", action="store_true", help="Sans caractères spéciaux"
    )
    gen.add_argument("--no-upper", action="store_true", help="Sans majuscules")
    gen.add_argument("--no-lower", action="store_true", help="Sans minuscules")

    # Commande pour ajouter un mot de passe
    add = subparsers.add_parser("add", help="Ajouter un mot de passe")
    add.add_argument("service", help="Nom du service")
    add.add_argument("username", help="Nom d'utilisateur")
    add.add_argument(
        "-p", "--password", help="Mot de passe (si non spécifié, sera généré)"
    )
    add.add_argument("-u", "--url", help="URL du service")
    add.add_argument("-n", "--notes", help="Notes additionnelles")

    # Commande pour obtenir un mot de passe
    get = subparsers.add_parser("get", help="Récupérer un mot de passe")
    get.add_argument("service", help="Nom du service")
    get.add_argument("username", nargs="?", help="Nom d'utilisateur")

    # Commande pour lister les mots de passe
    list_cmd = subparsers.add_parser("list", help="Lister tous les services")

    # Commande pour supprimer un mot de passe
    delete = subparsers.add_parser("delete", help="Supprimer un mot de passe")
    delete.add_argument("service", help="Nom du service")
    delete.add_argument("username", help="Nom d'utilisateur")

    # Commande pour rechercher des mots de passe
    search = subparsers.add_parser("search", help="Rechercher des services")
    search.add_argument(
        "query", help="Terme de recherche (service, utilisateur ou URL)"
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # Initialisation du vault
        master_password = getpass("Entrez votre mot de passe maître: ")
        keyring = Keyring()
        vault = Vault(Path("vault.db"))
        keyring.unlock(master_password, vault.kdf_params)

        if args.command == "generate":
            password = generate_password(
                length=args.length,
                use_digits=not args.no_digits,
                use_specials=not args.no_special,
                use_upper=not args.no_upper,
                use_lower=not args.no_lower,
            )
            print(f"Mot de passe généré: {password}")

        elif args.command == "add":
            password = args.password
            if not password:
                password = generate_password()

            vault.add_password(
                service=args.service,
                username=args.username,
                password=password,
                url=args.url,
                notes=args.notes,
            )
            print(f"Mot de passe ajouté pour {args.service} ({args.username})")

        elif args.command == "get":
            entry = vault.get_password(args.service, args.username)
            if entry:
                print(f"Service: {entry.service}")
                print(f"Utilisateur: {entry.username}")
                print(f"Mot de passe: {entry.password}")
                if entry.url:
                    print(f"URL: {entry.url}")
                if entry.notes:
                    print(f"Notes: {entry.notes}")
            else:
                print("Aucun mot de passe trouvé.")

        elif args.command == "list":
            entries = vault.list_passwords()
            if entries:
                print("Services enregistrés:")
                for entry in entries:
                    print(f"- {entry.service} ({entry.username})")
            else:
                print("Aucun mot de passe enregistré.")

        elif args.command == "delete":
            vault.delete_password(args.service, args.username)
            print(f"Mot de passe supprimé pour {args.service} ({args.username})")

        elif args.command == "search":
            results = vault.search(args.query)
            if results:
                print("Résultats de la recherche :")
                for e in results:
                    print(
                        f"[{e.id}] {e.title or e.service} — {e.username or ''} — {e.url or ''}"
                    )
            else:
                print("Aucun résultat.")

    except Exception as e:
        print(f"Erreur: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

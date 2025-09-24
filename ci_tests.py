#!/usr/bin/env python3
"""
Configuration des tests pour GitHub Actions.
Adapte l'exécution des tests pour l'environnement CI sans interface graphique.
"""

import os
import sys


# Configuration pour l'environnement CI
def setup_ci_environment():
    """Configure l'environnement pour les tests CI"""

    # Variables d'environnement pour Qt dans CI
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["DISPLAY"] = ":99.0"

    # Désactiver les interactions utilisateur
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    # Configuration pour éviter les erreurs graphiques
    if "GITHUB_ACTIONS" in os.environ:
        os.environ["QT_LOGGING_RULES"] = "qt.qpa.*=false"


def run_tests_for_ci():
    """Lance les tests adaptés pour l'environnement CI"""
    setup_ci_environment()

    import unittest

    # Tests qui ne nécessitent pas d'interface graphique
    safe_test_modules = [
        "tests.test_crypto",
        "tests.test_generator",
        "tests.test_storage",
        "tests.test_vault",
    ]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for module in safe_test_modules:
        try:
            module_suite = loader.loadTestsFromName(module)
            suite.addTest(module_suite)
        except Exception as e:
            print(f"⚠️ Impossible de charger {module}: {e}")

    # Lancer les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests_for_ci()
    sys.exit(0 if success else 1)

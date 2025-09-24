#!/usr/bin/env python3
"""
Setup script pour le gestionnaire de mots de passe sécurisé.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Lire le README pour la description longue
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Lire les requirements
requirements = (this_directory / "requirements.txt").read_text().strip().split("\n")
requirements = [
    req.strip() for req in requirements if req.strip() and not req.startswith("#")
]

setup(
    name="password-manager",
    version="1.0.0",
    author="Marie-Ange Kuitche",
    author_email="marie-ange@example.com",
    description="Gestionnaire de mots de passe sécurisé avec interface graphique",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/marie-angekuitche/password-manager",
    project_urls={
        "Bug Tracker": "https://github.com/marie-angekuitche/password-manager/issues",
        "Documentation": "https://github.com/marie-angekuitche/password-manager#readme",
        "Source Code": "https://github.com/marie-angekuitche/password-manager",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Security :: Cryptography",
        "Environment :: X11 Applications :: Qt",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "coverage>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "pyinstaller>=6.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "coverage>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "password-manager=ui.cli:main",
            "pwmgr=ui.cli:main",
        ],
        "gui_scripts": [
            "password-manager-gui=ui.app_qt:main",
        ],
    },
    package_data={
        "ui": ["*.qss", "*.ui"],
        "": ["*.md", "*.txt", "*.toml"],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="password manager security crypto vault encryption",
)

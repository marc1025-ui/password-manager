from setuptools import setup, find_packages

setup(
    name="password-manager",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "argon2-cffi",
        "pydantic",
        "sqlite-utils",
        "click",
        "rich",
        "PySide6",
    ],
    python_requires=">=3.9",
)

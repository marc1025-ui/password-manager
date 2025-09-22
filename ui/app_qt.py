from crypto.keyring import Keyring, KDFParams

# Simuler paramètres sauvegardés dans vault_meta
params = KDFParams(salt=b"1234567890abcdef")

kr = Keyring()
kr.unlock("motdepasse-maitre", params)

print("Clé dispo ? ->", kr.is_unlocked())
print("Clé AES en mémoire ->", kr.get_key().hex())

kr.lock()
print("Après lock ->", kr.is_unlocked())

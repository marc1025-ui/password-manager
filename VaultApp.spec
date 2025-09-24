# pyinstaller VaultApp.spec
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = []
# Qt / PySide6
hiddenimports += collect_submodules("PySide6")

# tes paquets internes (assure-toi qu'ils ont __init__.py)
hiddenimports += collect_submodules("ui")
hiddenimports += collect_submodules("core")
hiddenimports += collect_submodules("crypto")
hiddenimports += collect_submodules("storage")

# si tu utilises d'autres libs (ex: argon2-cffi), dé-commente :
# hiddenimports += collect_submodules("argon2")

datas = []
# Plugins Qt indispensables
datas += collect_data_files("PySide6", includes=[
    "Qt/plugins/platforms/*",
    "Qt/plugins/imageformats/*",
    "Qt/plugins/styles/*",
    "Qt/translations/*",
])

block_cipher = None

a = Analysis(
    ['ui/app_qt.py'],   # ← ton entrypoint
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='MaNelly',           # nom du .exe
    debug=False,
    strip=False,
    upx=False,                  # si ton antivirus rouspète, passe à False
    console=False,             # GUI: pas de console
    icon='assets/icon.ico',    # supprime la ligne si tu n'as pas d'icône
)

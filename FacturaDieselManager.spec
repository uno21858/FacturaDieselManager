# -*- mode: python ; coding: utf-8 -*-

import sys
import platform
from pathlib import Path

# Rutas del proyecto
project_dir = Path('.')
is_windows = platform.system() == 'Windows'
is_mac = platform.system() == 'Darwin'

block_cipher = None

# Datos adicionales (archivos UI, etc.)
datas = [
    ('Principal/UI/principal_window.ui', 'Principal/UI'),
    ('Credenciales/UI/credenciales_windows.ui', 'Credenciales/UI'),
]

# Incluir geckodriver.exe solo en Windows
if is_windows:
    geckodriver_path = project_dir / 'DescargaFacturasSAT' / 'geckodriver.exe'
    if geckodriver_path.exists():
        datas.append(('DescargaFacturasSAT/geckodriver.exe', 'DescargaFacturasSAT'))

# Archivos ocultos de importación
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.firefox',
    'selenium.webdriver.firefox.options',
    'selenium.webdriver.firefox.service',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'PIL',
    'xml.etree.ElementTree',
    'zstandard',
]

# Módulos a excluir (reduce el tamaño del ejecutable)
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'IPython',
    'jupyter',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FacturaDieselManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sin consola para una app más limpia
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Icons/icon.ico' if is_windows else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FacturaDieselManager',
)

# Para crear un .app en macOS solamente
if is_mac:
    app = BUNDLE(
        coll,
        name='FacturaDieselManager.app',
        icon=None,  # Puedes crear un .icns del .ico para macOS
        bundle_identifier='com.gasolinerocolon.facturadieselmanager',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.2.0',
        },
    )

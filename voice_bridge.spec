# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Voice Bridge executable.

Build with:
    cd C:\PROJECTS\RTSTT
    .\venv\Scripts\activate
    pyinstaller voice_bridge.spec
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Find NVIDIA DLL paths in the venv
venv_site = Path(os.environ.get('VIRTUAL_ENV', r'C:\PROJECTS\RTSTT\venv')) / 'Lib' / 'site-packages'
nvidia_bins = []
for pkg in ('cudnn', 'cublas', 'cuda_runtime', 'cufft', 'curand'):
    bin_dir = venv_site / 'nvidia' / pkg / 'bin'
    if bin_dir.is_dir():
        for dll in bin_dir.glob('*.dll'):
            nvidia_bins.append((str(dll), '.'))

# Collect ctranslate2 DLLs
ct2_dir = venv_site / 'ctranslate2'
ct2_bins = []
if ct2_dir.is_dir():
    for dll in ct2_dir.glob('*.dll'):
        ct2_bins.append((str(dll), 'ctranslate2'))

a = Analysis(
    ['src/voice_bridge/launcher.py'],
    pathex=['C:\\PROJECTS\\RTSTT'],
    binaries=nvidia_bins + ct2_bins,
    datas=[],
    hiddenimports=[
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
        'pynput._util',
        'pynput._util.win32',
        'pyperclip',
        'pyaudio',
        'pystray',
        'pystray._win32',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'faster_whisper',
        'ctranslate2',
        'numpy',
        'src.core.stt_engine.whisper_rtx',
        'src.core.audio_capture.audio_capture_base',
        'src.core.audio_capture.drivers.portaudio_driver',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'pytest'],
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
    name='VoiceBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # Keep console for logging
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='VoiceBridge',
)

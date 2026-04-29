# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for freezing the FoundrAI backend into a standalone binary."""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Collect data and submodules for key dependencies
chromadb_data = collect_data_files("chromadb")
litellm_data = collect_data_files("litellm")
certifi_data = collect_data_files("certifi")
onnxruntime_bins = collect_dynamic_libs("onnxruntime")

hidden_imports = [
    # Uvicorn internals
    *collect_submodules("uvicorn"),
    # Database
    "aiosqlite",
    "sqlite3",
    # ChromaDB
    *collect_submodules("chromadb"),
    "onnxruntime",
    # LiteLLM
    *collect_submodules("litellm"),
    # Tokenizers
    "tiktoken",
    "tiktoken_ext",
    "tiktoken_ext.openai_public",
    # LangChain
    *collect_submodules("langchain_community"),
    # Other
    "dotenv",
    "yaml",
    "pydantic",
    "fastapi",
    "starlette",
    "httptools",
    "uvloop" if sys.platform != "win32" else "asyncio",
    "websockets",
]

a = Analysis(
    ["../foundrai/desktop_main.py"],
    pathex=[],
    binaries=onnxruntime_bins,
    datas=[
        *chromadb_data,
        *litellm_data,
        *certifi_data,
        ("../foundrai/frontend/dist", "foundrai/frontend/dist"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "numpy.tests"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="foundrai-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Need stdout for PORT:{port} communication
)

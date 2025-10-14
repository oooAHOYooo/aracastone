# ArcaStone

Offline-first desktop PDF indexing and search app (PySide6), CleanMyMac-style UI.

## Features (MVP)
- Drag-and-drop PDFs to ingest into a content-addressed store (BLAKE3)
- Index text using sentence-transformers `all-MiniLM-L6-v2` and FAISS (CPU)
- Search and preview snippets; ranked results
- Export selected files to a folder/USB

## Requirements
- Python 3.11+
- PySide6, pypdf, sentence-transformers, faiss-cpu, blake3

## Install
```bash
# using Poetry (recommended)
pipx install poetry  # if needed
poetry install
```

### Dev (make target)
```make
dev:
	python -m venv .venv && . .venv/bin/activate && pip install -e .
```

## Model cache (offline-first)
This app does not make network calls. You must have the model locally cached.

1. On a machine with internet, download the model directory for `all-MiniLM-L6-v2` using sentence-transformers.
2. Copy the resulting directory into `data/models/`.
3. Ensure env is set automatically by the app to use `SENTENCE_TRANSFORMERS_HOME=data/models`.

## Run
```bash
poetry run python -m arcastone.app
```

## Tests
```bash
poetry run pytest -q
```

## Notes
- Optional OCR is supported via `ocrmypdf` when present in PATH.
- Data is stored under `data/` (blobs, index, models, manifest, tlog).

## Dev
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
python arcastone/app.py
```

## Usage
- Drag-and-drop PDFs in Ingest
- Click "Index Documents"
- Use Search to find pages/snippets
- Add to Export and export to a folder/USB

## Packaging (PyInstaller)
```bash
pip install pyinstaller
pyinstaller --name "ArcaStone" --windowed --noconfirm arcastone/app.py
```

### macOS Installer (DMG and PKG)

Prereqs: Xcode command line tools, optional Developer ID certs for signing.

1. Build the app bundle:
```bash
pyinstaller --name "ArcaStone" --windowed --noconfirm arcastone/app.py
```

2. Build a .pkg installer (installs to /Applications):
```bash
bash scripts/macos/build_pkg.sh
```

3. Build a .dmg with drag-to-Applications and an install helper:
```bash
python scripts/macos/build_dmg.py
```
Place `Install ArcaStone.command` and `ArcaStone.app` inside the DMG for a simple guided install.

Note: For distribution, sign and notarize the app and installer per Apple docs.

### System dependencies (optional for OCR)
- `ocrmypdf` and `tesseract` if you want OCR. Without them, text is extracted via `pypdf` only.

## Roadmap
- Encryption and key-wrap for stored objects and exports
- Scheduled backups / snapshots
- Read-only viewer for quick preview
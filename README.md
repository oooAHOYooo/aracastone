# ArcaStone

Offline-first desktop PDF indexing and search app (PySide6), flat classic Windows-style UI.

## Quick start (for anyone trying it out)

Your friend can run from source with Python 3.11; no private data is included. The app creates its own `data/` folder on first run.

```bash
# 1) Clone and enter the repo
git clone https://github.com/<you>/arcastone.git
cd arcastone

# 2) Create a venv and install deps
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

# 3) One-time: cache the embedding model locally (requires internet once)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='data/index/.models')"

# 4) Run
python app.py
```

Then drag-and-drop a few PDFs into Home → click “Index Documents” → Search.
Data is stored under `data/` in the project root and never leaves the machine.

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
# Quickstart with venv + pip (no Poetry required)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Dev (make target)
```make
dev:
	python -m venv .venv && . .venv/bin/activate && pip install -e .
```

## Model cache (offline-first)
This app runs offline by default. You must have models locally cached.

1. Embedding model (required): cache `all-MiniLM-L6-v2` under `data/index/.models`:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='data/index/.models')"
```
2. Local LLM for Q&A (optional, recommended: Qwen2.5 1.5B Instruct):
```bash
python scripts/models/prepare_local_llm.py \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --dst data/models/llm
```
Optionally set `ARCASTONE_LOCAL_LLM_PATH` to point to a custom location.

## Run
```bash
# from repo root, with the venv activated
python app.py
```

## Tests
```bash
poetry run pytest -q
```

## Notes
- Optional OCR is supported via `ocrmypdf` when present in PATH.
- Data is stored under `data/` (blobs, index, models, manifest, tlog). To reset, delete the `data/` folder.
- macOS tip: if FAISS complains about OpenMP, install `libomp` with Homebrew: `brew install libomp`.

## Dev
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -m arcastone.app
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

Q&A model with PyInstaller:
- The model directory is not bundled. Place Qwen locally (e.g., `data/models/llm`) and use Q&A → “Set Model Path…”.
- Ensure runtime includes `torch`, `transformers`, and `safetensors`. If freezing causes import issues, add hidden imports via a `.spec` file for transformers components.

## Fully offline bundle (copy everything)
To prepare a complete offline bundle of your vault, models, and indexes, copy the entire `data/` directory to the target machine:

```bash
python scripts/bundle_offline.py --dst /path/to/usb-or-target
```

On the target machine:
- Place `data/` next to the app bundle (or in the project root for the Python app).
- Open Q&A → “Set Model Path…” and select `data/models/llm`.

### System dependencies (optional for OCR)
- `ocrmypdf` and `tesseract` if you want OCR. Without them, text is extracted via `pypdf` only.

## Roadmap
- Encryption and key-wrap for stored objects and exports
- Scheduled backups / snapshots
- Read-only viewer for quick preview
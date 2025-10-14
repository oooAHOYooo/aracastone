from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Paths:
    base_dir: Path
    data_dir: Path
    blobs_dir: Path
    index_dir: Path
    models_dir: Path
    manifest_path: Path
    tlog_path: Path
    faiss_index_path: Path
    metadata_db_path: Path


def _discover_base_dir() -> Path:
    # Resolve to repo root assuming this file is at arcastone/core/config.py
    return Path(__file__).resolve().parents[2]


BASE_DIR: Path = _discover_base_dir()
DATA_DIR: Path = BASE_DIR / "data"
BLOBS_DIR: Path = DATA_DIR / "blobs"
INDEX_DIR: Path = DATA_DIR / "index"
MODELS_DIR: Path = DATA_DIR / "models"
MANIFEST_PATH: Path = DATA_DIR / "manifest.json"
TLOG_PATH: Path = DATA_DIR / "tlog.jsonl"
FAISS_INDEX_PATH: Path = INDEX_DIR / "index.faiss"
METADATA_DB_PATH: Path = INDEX_DIR / "metadata.sqlite3"


def ensure_directories() -> None:
    """Create required directories if missing."""
    for path in [DATA_DIR, BLOBS_DIR, INDEX_DIR, MODELS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def set_offline_model_cache_env() -> None:
    """Set environment variable for sentence-transformers cache location.

    This helps offline usage by keeping the model in a local project cache.
    """
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(MODELS_DIR))


MODEL_NAME: str = "all-MiniLM-L6-v2"
EMBEDDING_DIM: int = 384

PATHS = Paths(
    base_dir=BASE_DIR,
    data_dir=DATA_DIR,
    blobs_dir=BLOBS_DIR,
    index_dir=INDEX_DIR,
    models_dir=MODELS_DIR,
    manifest_path=MANIFEST_PATH,
    tlog_path=TLOG_PATH,
    faiss_index_path=FAISS_INDEX_PATH,
    metadata_db_path=METADATA_DB_PATH,
)



from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import os
import sqlite3

import numpy as np
import faiss  # type: ignore
from sentence_transformers import SentenceTransformer

from .storage import ensure_subdirs
from .pdf import extract_text, first_snippet


# Paths
SUBS = ensure_subdirs()
DATA_DIR = SUBS["objects"].parents[0]
INDEX_DIR = DATA_DIR / "index"
INDEX_DIR.mkdir(parents=True, exist_ok=True)
FAISS_PATH = INDEX_DIR / "faiss.index"
MODEL_CACHE = INDEX_DIR / ".models"
CATALOG_DB = DATA_DIR / "catalog.sqlite"


_EMBEDDER: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _EMBEDDER
    if _EMBEDDER is None:
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=str(MODEL_CACHE))
    return _EMBEDDER


def _normalize(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / n


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(CATALOG_DB))
    return conn


def init_index() -> None:
    # Ensure sqlite schema
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                name TEXT,
                hash TEXT UNIQUE,
                size INT,
                stored_path TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY,
                file_id INT,
                page INT,
                text TEXT,
                snippet TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    # Ensure FAISS file exists (create empty index if missing)
    if not FAISS_PATH.exists():
        emb = get_embedder()
        dim = int(emb.get_sentence_embedding_dimension())
        base = faiss.IndexFlatIP(dim)
        idx = faiss.IndexIDMap2(base)
        faiss.write_index(idx, str(FAISS_PATH))


def _open_index() -> faiss.Index:
    return faiss.read_index(str(FAISS_PATH))


def register_file(meta: Dict[str, object]) -> int:
    """Upsert file metadata into the catalog and return file id.

    Expected keys in meta: name, hash, size, stored_path
    """
    init_index()
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO files(name, hash, size, stored_path)
            VALUES(?,?,?,?)
            ON CONFLICT(hash) DO UPDATE SET
                name=excluded.name,
                size=excluded.size,
                stored_path=excluded.stored_path
            """,
            (meta.get("name"), meta.get("hash"), meta.get("size"), meta.get("stored_path")),
        )
        conn.commit()
        # fetch id
        cur.execute("SELECT id FROM files WHERE hash=?", (meta.get("hash"),))
        row = cur.fetchone()
        return int(row[0]) if row else -1
    finally:
        conn.close()


def _split_long(text: str, max_chars: int = 1200, overlap: int = 120) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def index_pdf(stored_path: Path, meta: Dict[str, object]) -> int:
    """Index a PDF: register file, extract text, chunk, embed, write to faiss.

    Returns number of chunks indexed.
    """
    init_index()
    file_id = register_file(meta)
    if file_id <= 0:
        return 0
    # Extract text per page
    items = extract_text(stored_path)
    # Prepare chunk rows
    conn = _conn()
    try:
        cur = conn.cursor()
        chunk_texts: List[str] = []
        chunk_rows: List[int] = []
        for it in items:
            page_no = int(it["page"]) if "page" in it else 0
            page_text = str(it.get("text", ""))
            for chunk in _split_long(page_text):
                snip = first_snippet(chunk)
                cur.execute(
                    "INSERT INTO chunks(file_id, page, text, snippet) VALUES(?,?,?,?)",
                    (file_id, page_no, chunk, snip),
                )
                chunk_id = cur.lastrowid
                chunk_rows.append(int(chunk_id))
                chunk_texts.append(chunk)
        conn.commit()
    finally:
        conn.close()
    if not chunk_texts:
        return 0
    # Embed
    emb = get_embedder()
    vecs = emb.encode(chunk_texts, batch_size=32, convert_to_numpy=True, show_progress_bar=False)
    vecs = vecs.astype(np.float32)
    vecs = _normalize(vecs)
    # Append to FAISS with IDs mapping to chunk ids
    index = _open_index()
    ids = np.array(chunk_rows, dtype=np.int64)
    index.add_with_ids(vecs, ids)
    faiss.write_index(index, str(FAISS_PATH))
    return len(chunk_rows)


def search(query: str, top_k: int = 10) -> List[Dict[str, object]]:
    """Search the FAISS index and return ranked results with metadata.

    Returns list of dicts: {score, file, page, snippet, hash}
    """
    init_index()
    if not FAISS_PATH.exists():
        return []
    index = _open_index()
    if index.ntotal == 0:
        return []
    emb = get_embedder()
    q = emb.encode([query], convert_to_numpy=True).astype(np.float32)
    q = _normalize(q)
    D, I = index.search(q, max(1, min(top_k, index.ntotal)))
    ids = [int(i) for i in I[0] if int(i) >= 0]
    scores = [float(s) for s in D[0][: len(ids)]]
    if not ids:
        return []
    # Fetch chunk + file metadata
    conn = _conn()
    try:
        cur = conn.cursor()
        qmarks = ",".join(["?"] * len(ids))
        cur.execute(f"SELECT id, file_id, page, snippet FROM chunks WHERE id IN ({qmarks})", ids)
        chunk_rows = {int(r[0]): (int(r[1]), int(r[2]), r[3]) for r in cur.fetchall()}
        file_ids = list({fid for (fid, _, _) in chunk_rows.values()})
        if file_ids:
            qf = ",".join(["?"] * len(file_ids))
            cur.execute(f"SELECT id, name, hash FROM files WHERE id IN ({qf})", file_ids)
            file_rows = {int(r[0]): (r[1], r[2]) for r in cur.fetchall()}
        else:
            file_rows = {}
    finally:
        conn.close()
    results: List[Dict[str, object]] = []
    for cid, score in zip(ids, scores):
        meta = chunk_rows.get(cid)
        if not meta:
            continue
        fid, page, snippet = meta
        fname, fhash = file_rows.get(fid, ("", ""))
        results.append({
            "score": score,
            "file": fname,
            "page": page,
            "snippet": snippet,
            "hash": fhash,
        })
    return results



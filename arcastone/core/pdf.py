from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import shutil
import subprocess
import tempfile

from pypdf import PdfReader


def is_pdf(path: Path) -> bool:
    """Heuristically determine if a file is a PDF.

    Checks extension and magic header.
    """
    if not path.exists() or not path.is_file():
        return False
    if path.suffix.lower() == ".pdf":
        return True
    try:
        with path.open("rb") as f:
            header = f.read(5)
        return header == b"%PDF-"
    except Exception:
        return False


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.split())


def extract_text(pdf_path: Path) -> List[Dict[str, object]]:
    """Extract text from a PDF into a list of {"page": int, "text": str}.

    - Uses pypdf for text extraction
    - Handles encoding issues and exceptions gracefully
    - Whitespace is normalized
    """
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        # Return empty extraction on failure, callers can decide next steps
        return []
    items: List[Dict[str, object]] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
        except Exception:
            text = ""
        items.append({"page": i, "text": _normalize_text(text)})
    return items


def _ocr_available() -> bool:
    try:
        res = subprocess.run(["ocrmypdf", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return res.returncode == 0
    except FileNotFoundError:
        return False


def ocr_if_needed(pdf_path: Path) -> Path:
    """Run OCR with `ocrmypdf` if most pages lack extractable text.

    - If >80% of sampled pages have no text, and `ocrmypdf` is present, run OCR
    - Writes to a temp file and returns that path; otherwise returns original
    - Sampling up to first 32 pages for speed on large PDFs
    """
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return pdf_path
    total_pages = len(reader.pages)
    sample_n = min(total_pages, 32)
    empty = 0
    for i in range(sample_n):
        try:
            text = reader.pages[i].extract_text()
        except Exception:
            text = ""
        if not _normalize_text(text):
            empty += 1
    if sample_n > 0 and (empty / sample_n) > 0.8 and _ocr_available():
        tmpdir = Path(tempfile.mkdtemp(prefix="arcastone-ocr-"))
        out = tmpdir / f"{pdf_path.stem}-ocr.pdf"
        try:
            result = subprocess.run(
                ["ocrmypdf", "--skip-text", str(pdf_path), str(out)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode == 0 and out.exists():
                return out
        except Exception:
            pass
    return pdf_path


def first_snippet(text: str, max_chars: int = 240) -> str:
    """Return a short snippet of text, trimmed to max_chars with ellipsis."""
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1].rstrip() + "…"


# Backwards compatibility for earlier internal API
def extract_text_by_page(pdf_path: Path) -> List[str]:  # pragma: no cover - thin wrapper
    return [item["text"] for item in extract_text(pdf_path)]

def count_pages(pdf_path: Path) -> int:  # pragma: no cover - thin wrapper
    try:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception:
        return 0



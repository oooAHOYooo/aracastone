from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import os

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from .index import search as vector_search
from .config import MODELS_DIR


_LLM = None
_TOKENIZER = None


@dataclass(frozen=True)
class QAResult:
    answer: str
    used_files: List[str]


def _get_llm_paths() -> Optional[Path]:
    explicit = os.environ.get("ARCASTONE_LOCAL_LLM_PATH", "").strip()
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    # default location inside data/models/llm
    p = MODELS_DIR / "llm"
    return p if p.exists() else None


def set_local_llm_path(path: str) -> bool:
    """Set (or clear) the preferred on-disk local LLM path.

    - When set, it overrides the default lookup under MODELS_DIR/llm.
    - Clears any cached tokenizer/model so the next use reloads from disk.
    Returns True if the provided path exists; False otherwise.
    """
    global _LLM, _TOKENIZER
    p = Path(path).expanduser() if path else None
    if p and p.exists():
        os.environ["ARCASTONE_LOCAL_LLM_PATH"] = str(p)
        _LLM = None
        _TOKENIZER = None
        return True
    # Clear override when invalid
    if "ARCASTONE_LOCAL_LLM_PATH" in os.environ:
        os.environ.pop("ARCASTONE_LOCAL_LLM_PATH", None)
    _LLM = None
    _TOKENIZER = None
    return False


def llm_status() -> Tuple[bool, Optional[str]]:
    """Return (available, path) for the local LLM directory."""
    p = _get_llm_paths()
    return (p is not None, str(p) if p else None)


def get_local_llm():
    """Load a local HF model from disk only.

    Returns (tokenizer, model) or (None, None) if not available.
    """
    global _LLM, _TOKENIZER
    if _LLM is not None and _TOKENIZER is not None:
        return _TOKENIZER, _LLM

    model_path = _get_llm_paths()
    if model_path is None:
        return None, None
    try:
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        # First attempt: standard load (most models)
        tok = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            local_files_only=True,
            low_cpu_mem_usage=True,
            torch_dtype=torch.float32,
        )
    except Exception:
        # Fallback for models requiring custom code (e.g., some Qwen variants)
        try:
            tok = AutoTokenizer.from_pretrained(
                str(model_path), local_files_only=True, trust_remote_code=True
            )
            model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                local_files_only=True,
                low_cpu_mem_usage=True,
                torch_dtype=torch.float32,
                trust_remote_code=True,
            )
        except Exception:
            return None, None
    model.to(torch.device("cpu"))
    model.eval()
    _TOKENIZER, _LLM = tok, model
    return tok, model


def build_context(query: str, top_k: int = 5) -> tuple[str, List[str]]:
    """Return a compact context string and list of files for a query."""
    hits = vector_search(query, top_k)
    lines: List[str] = []
    files: List[str] = []
    for h in hits:
        fname = str(h.get("file", ""))
        page = int(h.get("page", 0))
        snippet = str(h.get("snippet", ""))
        files.append(fname)
        lines.append(f"- {fname} (p.{page}): {snippet}")
    return "\n".join(lines), files


def generate_answer(question: str, top_k: int = 5, max_new_tokens: int = 128) -> QAResult:
    """Generate a local answer using retrieved snippets.

    Falls back to extractive summary if a local LLM is not available.
    """
    context, files = build_context(question, top_k=top_k)
    if not context:
        return QAResult(answer="No relevant context found in the local index.", used_files=[])

    tok, llm = get_local_llm()
    if tok is None or llm is None:
        # Extractive fallback
        preface = (
            "Local LLM not found. Returning a summary from the most relevant passages:\n\n"
        )
        return QAResult(answer=preface + context, used_files=files)

    prompt = (
        "You are a concise assistant. Answer the question using only the provided context.\n"
        "Cite filenames and page numbers when relevant. If unsure, say you don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\nAnswer:"
    )

    device = torch.device("cpu")
    inputs = tok(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = llm.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.2,
            pad_token_id=tok.eos_token_id,
        )
    text = tok.decode(out[0], skip_special_tokens=True)
    # Extract only the completion after 'Answer:'
    answer = text.split("Answer:", 1)[-1].strip()
    return QAResult(answer=answer, used_files=files)



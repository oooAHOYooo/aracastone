#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Download a local HF LLM for ArcaStone")
    parser.add_argument(
        "--model",
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        help="Hugging Face model id to download (default: TinyLlama/TinyLlama-1.1B-Chat-v1.0)",
    )
    parser.add_argument(
        "--dst",
        default=str(Path(__file__).resolve().parents[2] / "data" / "models" / "llm"),
        help="Destination directory to store the model (default: data/models/llm)",
    )
    args = parser.parse_args()

    # Ensure destination exists
    dst = Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    # Prefer offline-friendly settings during normal app use; allow download here.
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    try:
        from huggingface_hub import snapshot_download  # type: ignore
    except Exception:
        print("Installing huggingface_hub…")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub>=0.20.0"])  # noqa: S603, S607
        from huggingface_hub import snapshot_download  # type: ignore

    print(f"Downloading {args.model} → {dst} …")
    snapshot_download(
        repo_id=args.model,
        local_dir=str(dst),
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=[
            "*.json",
            "*.safetensors",
            "*.bin",
            "*.txt",
            "tokenizer.*",
            "vocab.*",
            "merges.txt",
            "config.json",
            "generation_config.json",
        ],
    )

    print("Verifying load with transformers (local files only)…")
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM  # type: ignore
        tok = AutoTokenizer.from_pretrained(str(dst), local_files_only=True)
        _ = AutoModelForCausalLM.from_pretrained(str(dst), local_files_only=True)
        print(f"Success. Model cached at: {dst}")
        print("Set ARCASTONE_LOCAL_LLM_PATH to override location if needed.")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Downloaded, but failed to verify model load: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())



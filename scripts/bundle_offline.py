#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import sys


def copy_tree(src: Path, dst: Path) -> None:
    """Copy a directory tree from src to dst, preserving metadata.

    If dst exists, files are overwritten; directories are created as needed.
    """
    if not src.exists() or not src.is_dir():
        raise SystemExit(f"Source directory not found: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle ArcaStone offline data for transfer")
    parser.add_argument(
        "--dst",
        required=True,
        help="Destination directory where the data/ folder will be copied",
    )
    parser.add_argument(
        "--src",
        default=None,
        help="Optional source project root (defaults to auto-detected repo root)",
    )
    args = parser.parse_args()

    if args.src:
        base = Path(args.src)
    else:
        # Assume this script lives in scripts/ under the repo root
        base = Path(__file__).resolve().parents[1]

    data_src = base / "data"
    data_dst = Path(args.dst).expanduser().resolve() / "data"

    print(f"Copying {data_src} -> {data_dst}")
    copy_tree(data_src, data_dst)
    print("Done. You can point the app at this data directory on the offline machine.")
    print("Tip: In Q&A, use ‘Set Model Path…’ to select data/models/llm on the target.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



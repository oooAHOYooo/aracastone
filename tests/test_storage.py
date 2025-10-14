from pathlib import Path
import tempfile

from arcastone.core.storage import blake3_file, store_file, resolve_object, ensure_subdirs


def test_compute_and_store_roundtrip(tmp_path: Path):
    ensure_subdirs()
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world", encoding="utf-8")
    digest = blake3_file(sample)
    info = store_file(sample)
    assert info["hash"] == f"b3:{digest}"
    obj_path = resolve_object(digest)
    assert obj_path.exists()



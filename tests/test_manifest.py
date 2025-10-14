from arcastone.core.manifest import DocumentEntry, add_document_entry, list_documents
from arcastone.core.config import ensure_directories


def test_manifest_add_and_list(tmp_path):
    ensure_directories()
    entry = DocumentEntry(
        digest="deadbeef",
        original_filename="doc.pdf",
        size_bytes=123,
        added_at="2024-01-01T00:00:00.000Z",
        pages_count=2,
    )
    add_document_entry(entry)
    docs = list_documents()
    assert any(d["digest"] == "deadbeef" for d in docs)



from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import sqlite3

from .index import _conn
from .manifest import list_documents


@dataclass(frozen=True)
class SiteNode:
    title: str
    digest: str
    pages: int


def build_sitemap() -> List[SiteNode]:
    """Return a flat list of documents for a simple sitemap view."""
    docs = list_documents()
    nodes: List[SiteNode] = []
    for d in docs:
        nodes.append(
            SiteNode(
                title=str(d.get("original_filename", "")),
                digest=str(d.get("digest", "")),
                pages=int(d.get("pages_count", 0)),
            )
        )
    return nodes


def export_sitemap_markdown() -> str:
    """Export a markdown index of all documents and their first snippet per file."""
    nodes = build_sitemap()
    out: List[str] = ["# Vault Sitemap", ""]
    if not nodes:
        out.append("(empty)")
        return "\n".join(out)
    # Fetch one snippet per file from chunks table
    conn = _conn()
    try:
        cur = conn.cursor()
        for n in nodes:
            out.append(f"- **{n.title}**  ")
            cur.execute(
                "SELECT page, snippet FROM chunks c JOIN files f ON f.id=c.file_id WHERE f.hash=? ORDER BY c.id ASC LIMIT 1",
                (n.digest,),
            )
            row = cur.fetchone()
            if row:
                out.append(f"  p.{int(row[0])}: {str(row[1])}")
    finally:
        conn.close()
    return "\n".join(out)



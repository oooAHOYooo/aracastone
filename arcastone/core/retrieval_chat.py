from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .index import search as vector_search


@dataclass(frozen=True)
class RetrievalAnswer:
    markdown: str
    sources: List[str]


def retrieve_only_answer(query: str, top_k: int = 5) -> RetrievalAnswer:
    """Return a non-generative answer built only from existing snippets.

    The response is markdown composed of quoted passages and citations.
    """
    hits = vector_search(query, top_k)
    if not hits:
        return RetrievalAnswer(markdown="No matching passages found in your vault.", sources=[])

    lines: List[str] = [f"### Results for: {query}", ""]
    sources: List[str] = []
    seen = set()
    for h in hits:
        fname = str(h.get("file", ""))
        page = int(h.get("page", 0))
        snippet = str(h.get("snippet", ""))
        cite = f"{fname} (p.{page})"
        lines.append(f"> {snippet}")
        lines.append(f"\n— {cite}\n")
        if fname and fname not in seen:
            seen.add(fname)
            sources.append(cite)
    return RetrievalAnswer(markdown="\n".join(lines), sources=sources)



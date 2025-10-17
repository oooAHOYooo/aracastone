from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser


class AboutPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        layout.addWidget(self.viewer)
        self.load_whitepaper()

    def load_whitepaper(self) -> None:
        today = datetime.now().strftime("%B %d, %Y")
        html = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {{
      font-family: -apple-system, system-ui, "SF Pro Text", Segoe UI, Roboto, Arial, sans-serif;
      color: #1C1C1E; margin: 24px; line-height: 1.55;
    }}
    h1 {{ font-size: 28px; margin: 0 0 16px; }}
    h2 {{ font-size: 20px; margin: 24px 0 8px; }}
    h3 {{ font-size: 16px; margin: 18px 0 6px; }}
    .muted {{ color: #4A4A4A; }}
    .tag {{ display:inline-block; background:#F7F7FA; border:1px solid #E6E6EE; padding:2px 8px; border-radius:10px; font-size:12px; margin-right:6px; }}
    .card {{ background:#FFFFFF; border:1px solid #E6E6EE; border-radius:14px; padding:16px; margin:14px 0; }}
    ul {{ margin: 6px 0 12px 22px; }}
    li {{ margin: 4px 0; }}
    code {{ background:#f3f3f6; padding:1px 5px; border-radius:6px; }}
    .kbd {{ font-family: ui-monospace, Menlo, monospace; font-size: 12px; background:#f3f3f6; padding:1px 6px; border-radius:6px; border:1px solid #e6e6ee; }}
    .grid {{ display:grid; gap:12px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
  </style>
  <title>ArcaStone Whitepaper</title>
  </head>
  <body>
    <h1>ArcaStone — Personal Offline Vault for Knowledge</h1>
    <div class="muted">Version 0.1 • Updated {today}</div>

    <div class="card">
      <h2>Executive Summary</h2>
      <p>ArcaStone is a desktop application that ingests, indexes, and searches personal documents entirely offline. The system turns unstructured PDFs into a portable, encrypted-ready “vault” that enables instant, natural-language search without cloud dependence. The near-term market is creators, academics, and professionals seeking durable, private knowledge preservation. Long-term, ArcaStone becomes a household <em>digital estate</em> product.</p>
    </div>

    <div class="card">
      <h2>MVP Goals</h2>
      <ul>
        <li><span class="tag">Done</span> Ingest PDFs into a content-addressed local store (BLAKE3, de-dup).</li>
        <li><span class="tag">Done</span> Index text with local embeddings (<code>all-MiniLM-L6-v2</code>) and FAISS.</li>
        <li><span class="tag">Done</span> Search with natural language and view ranked snippets (offline-only).</li>
        <li><span class="tag">Done</span> Export selected originals to a destination folder/USB.</li>
        <li><span class="tag">Optional</span> Local Q&A over your vault — recommended model: <code>Qwen/Qwen2.5-1.5B-Instruct</code>. Configure under <em>Q&A</em> tab (“Set Model Path…”).</li>
      </ul>
    </div>

    <h2>Problem</h2>
    <ul>
      <li><b>Fragmented archives</b>: Research and creative work is scattered across drives, email, and SaaS silos.</li>
      <li><b>Trust and privacy</b>: Cloud AI features mean data leaves user control; compliance and consent are unclear.</li>
      <li><b>Loss over time</b>: File formats, accounts, and links rot; heirs lack a transferable archive.</li>
    </ul>

    <h2>Solution</h2>
    <p>ArcaStone offers a <b>local-first vault</b>: content-addressed storage, transparent indexes, and fast semantic search on the user’s own machine. The vault is portable and future-ready for encryption and replication.</p>

    <h2>Product Overview</h2>
    <div class="grid">
      <div class="card">
        <h3>Ingest</h3>
        <ul>
          <li>Drag-and-drop PDFs; BLAKE3 content addressing prevents duplicates.</li>
          <li>Text via <code>pypdf</code>; optional OCR fallback when available.</li>
          <li>Every action logged to a manifest + append-only transaction log.</li>
        </ul>
      </div>
      <div class="card">
        <h3>Index</h3>
        <ul>
          <li>Per-page chunking; embeddings with <code>all-MiniLM-L6-v2</code>.</li>
          <li>Local FAISS index; SQLite for file/chunk metadata.</li>
          <li>Rebuildable at any time for maintenance.</li>
        </ul>
      </div>
      <div class="card">
        <h3>Search</h3>
        <ul>
          <li>Natural-language queries return ranked results with snippets.</li>
          <li>No network calls; predictable performance and privacy.</li>
        </ul>
      </div>
      <div class="card">
        <h3>Export</h3>
        <ul>
          <li>Select items to export; preserve original filenames where possible.</li>
          <li>Simple, transparent folder output (USB-friendly).</li>
        </ul>
      </div>
    </div>

    <h2>Architecture</h2>
    <ul>
      <li><b>Local-only</b>: All compute and data stay on device by default.</li>
      <li><b>Data layout</b> under <span class="kbd">data/</span>:
        <ul>
          <li><span class="kbd">objects/</span> — files stored by hash</li>
          <li><span class="kbd">index/</span> — FAISS index + SQLite metadata</li>
          <li><span class="kbd">models/</span> — cached embeddings model</li>
          <li><span class="kbd">manifests/</span>, <span class="kbd">tlog/</span> — provenance + audit trail</li>
        </ul>
      </li>
      <li><b>Deterministic primitives</b>: BLAKE3 for addressing; append-only logs for integrity.</li>
      <li><b>Extendable</b>: Future layers add encryption, replication, and additional file types.</li>
    </ul>

    <h2>Security & Privacy</h2>
    <ul>
      <li>Offline-first by design; no background telemetry.</li>
      <li>Clear boundary between <em>originals</em> and <em>derived indexes</em>.</li>
      <li>Planned: per-vault encryption, key rotation, notarized timestamps.</li>
    </ul>

    <h2>User Experience</h2>
    <ul>
      <li>Clean, approachable desktop UI (macOS-style) with sidebar navigation.</li>
      <li>Progress and toasts for background operations (ingest, index, export).</li>
      <li>Natural-language search and one-click export flow.</li>
    </ul>

    <h2>Go-to-Market</h2>
    <ul>
      <li><b>Bespoke onboarding</b>: hand-set up early customer vaults (trust > software).</li>
      <li><b>Early segments</b>: professors, writers, indie musicians, consultants, families.</li>
      <li><b>Pricing</b> (indicative): setup $300–$800; ingest sessions $200–$500; plugin add-ons $100–$500; optional annual maintenance $100–$200.</li>
    </ul>

    <h2>Roadmap</h2>
    <ul>
      <li>Encryption + key management; replication/snapshots.</li>
      <li>Additional formats (images, docs, markdown).</li>
      <li>Local lightweight LLM for Q&A over private data.</li>
      <li>Read-only estate mode and optional sync layer.</li>
    </ul>

    <h2>Why Now</h2>
    <p>As AI adoption accelerates, individuals and small teams need <b>private AI</b>—capabilities without surrendering data. Commodity local embeddings + fast vector search make ArcaStone feasible today.</p>

    <h2>Appendix: Technology Stack</h2>
    <ul>
      <li>GUI: PySide6 • Extraction: pypdf (+ OCR when present)</li>
      <li>Index: FAISS + sentence-transformers • Metadata: SQLite</li>
      <li>Concurrency: QThreads • Packaging: PyInstaller</li>
    </ul>
  </body>
</html>'''
        self.viewer.setHtml(html)



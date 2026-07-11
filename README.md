# CoverIndex AI

CoverIndex AI is a vectorless, page-indexed RAG system for insurance policy queries.
It is designed to answer questions from the provided policy PDFs with citations and a
strict "answer only from evidence" flow.

## What it does

- Ingests insurance PDFs from a directory or a ZIP archive.
- Builds a page index instead of embeddings.
- Routes queries to the most relevant insurer or policy family.
- Retrieves the best matching pages with a BM25-style lexical scorer.
- Verifies the answer against the retrieved evidence before responding.
- Serves a clean insurance-assistant UI with citation cards.

## How the pipeline works

1. `RouterAgent` detects the insurer, product hints, and query intent.
2. `PageIndexRetriever` ranks pages using lexical overlap and page metadata.
3. `EvidenceAssembler` collects the strongest source pages and neighboring context.
4. `Verifier` checks that the final answer is grounded in the retrieved text.
5. The UI displays the verified answer plus exact document citations.

## Folder structure

- `policy_rag/` - ingestion, page indexing, routing, and answer generation
- `public/` - frontend HTML, CSS, and browser logic
- `worker.js` - Cloudflare Worker that serves the latest `public/` frontend and proxies API calls
- `cache/` - generated index cache

## Running locally

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:

   ```bash
   python app.py
   ```

3. Open `http://localhost:8000`.

The local server serves the UI directly from `public/`, so the latest frontend in GitHub
is the same frontend you will see when running `python app.py`.

## Cloudflare deployment

The Cloudflare Worker in `worker.js` uses the same frontend source of truth:

- static UI comes from `public/index.html`, `public/styles.css`, and `public/app.js`
- API requests under `/api/*` are proxied to `https://coverindex-ai.onrender.com`

That means:

- local runs use `public/`
- GitHub contains the latest working UI in `public/`
- Cloudflare deploys can use `worker.js` without relying on an outdated bundled copy

## Document source

The server automatically looks for documents in this order:

- `POLICY_DOCS_SOURCE` environment variable
- `data/policies`
- `data/policies.zip`
- `C:\Users\ADMIN\OneDrive\Downloads\Policy Documents.zip`

You can point `POLICY_DOCS_SOURCE` to either a folder of PDFs or the ZIP archive.

## Why this is vectorless

The system never depends on embeddings or a vector database. It uses:

- page-level text extraction,
- token frequency scoring,
- query routing,
- and evidence verification.

That makes the retrieval path easier to explain, audit, and debug for high-stakes
insurance use cases.

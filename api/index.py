from __future__ import annotations

import json
import os
import re
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Ensure project root is importable from serverless context
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Lazy-cached singletons ───────────────────────────────────────────────────
_INDEX = None


def _get_index():
    global _INDEX
    if _INDEX is None:
        from policy_rag.index import PageIndex
        _INDEX = PageIndex.load()
    return _INDEX



# ── Vercel serverless handler ────────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    server_version = "CoverIndexAI/1.0"

    # ------------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            try:
                index = _get_index()
                self._json({
                    "ready": True,
                    "page_count": len(index.records),
                    "document_count": index.document_count,
                    "signature": index.signature,
                })
            except Exception as exc:
                self._json({"ready": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if path == "/api/policies":
            try:
                index = _get_index()
                docs: dict = {}
                for record in index.records:
                    if record.doc_id not in docs:
                        docs[record.doc_id] = {
                            "doc_id": record.doc_id,
                            "file_name": record.file_name,
                            "insurer": record.insurer,
                            "product": record.product,
                            "document_type": record.document_type,
                            "page_count": 0,
                            "title": record.title,
                        }
                    docs[record.doc_id]["page_count"] += 1
                doc_list = sorted(docs.values(), key=lambda d: (d["insurer"], d["product"]))
                self._json({"policies": doc_list})
            except Exception as exc:
                self._json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # Static files — served by /web/ rewrite, but handle root just in case
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    # ------------------------------------------------------------------
    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        # ── /api/ask ──────────────────────────────────────────────────
        if path == "/api/ask":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length).decode("utf-8")
                payload = json.loads(raw or "{}")
                query = str(payload.get("query", "")).strip()
                file_name = payload.get("file_name")
                if file_name:
                    file_name = str(file_name).strip()
            except Exception as exc:
                self.send_error(HTTPStatus.BAD_REQUEST, f"Invalid JSON: {exc}")
                return

            if not query:
                self._json({"error": "Query is required"}, HTTPStatus.BAD_REQUEST)
                return

            try:
                from policy_rag.agent import answer_query
                index = _get_index()
                result = answer_query(index, query, file_name=file_name)
                self._json({
                    "answer": result.answer,
                    "confidence": result.confidence,
                    "route": {
                        "insurer": result.route.insurer,
                        "product_hint": result.route.product_hint,
                        "intent": result.route.intent,
                        "reasoning": result.route.reasoning,
                    },
                    "sources": result.sources,
                    "trace": result.trace,
                })
            except Exception as exc:
                self._json({"error": f"Query failed: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # ── /api/upload ───────────────────────────────────────────────
        if path == "/api/upload":
            try:
                content_type = self.headers.get("Content-Type", "")
                if not content_type.startswith("multipart/form-data"):
                    self._json({"error": "Content-Type must be multipart/form-data"}, HTTPStatus.BAD_REQUEST)
                    return

                boundary = content_type.split("boundary=")[1].encode("utf-8")
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)

                parts = body.split(b"--" + boundary)
                file_data = None
                filename = "uploaded_document.pdf"
                for part in parts:
                    if b"filename=" in part:
                        headers_part, content_part = part.split(b"\r\n\r\n", 1)
                        content_part = content_part.rsplit(b"\r\n", 1)[0]
                        fn_match = re.search(rb'filename="([^"]+)"', headers_part)
                        if fn_match:
                            filename = fn_match.group(1).decode("utf-8", errors="ignore")
                        file_data = content_part
                        break

                if not file_data:
                    self._json({"error": "No file found in request"}, HTTPStatus.BAD_REQUEST)
                    return

                from policy_rag.ingest import extract_records_from_pdf
                index = _get_index()
                records = extract_records_from_pdf(file_data, filename, f"uploaded/{filename}")

                if not records:
                    self._json({"error": "Failed to extract text from PDF (empty or encrypted)"}, HTTPStatus.BAD_REQUEST)
                    return

                index.records.extend(records)
                index.document_count = len({r.doc_id for r in index.records})
                for record in records:
                    for term in record.token_counts:
                        index.document_frequency[term] = index.document_frequency.get(term, 0) + 1

                self._json({
                    "success": True,
                    "filename": filename,
                    "page_count": len(records),
                    "total_pages": len(index.records),
                    "total_documents": index.document_count,
                })
            except Exception as exc:
                self._json({"error": f"Upload failed: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    # ------------------------------------------------------------------
    def _json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

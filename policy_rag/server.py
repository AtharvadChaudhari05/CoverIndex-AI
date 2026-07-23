from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .agent import (
    OUT_OF_SCOPE_REFUSAL_MESSAGE,
    answer_query,
    classify_query_scope,
    is_confirmation_query,
    route_query,
)
from .config import WEB_DIR, allow_out_of_scope_answers, require_fallback_confirmation
from .index import PageIndex
from .models import ConversationState, QueryResult


INDEX: PageIndex | None = None
SESSION_STATES: dict[str, ConversationState] = {}


def ensure_index() -> PageIndex:
    global INDEX
    if INDEX is None:
        INDEX = PageIndex.load()
    return INDEX


def ensure_session_state(session_id: str) -> ConversationState:
    state = SESSION_STATES.get(session_id)
    if state is None:
        state = ConversationState()
        SESSION_STATES[session_id] = state
    return state


class PolicyLensHandler(BaseHTTPRequestHandler):
    server_version = "PolicyLensAI/1.0"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Content-Length")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self._send_json(
                {
                    "ready": True,
                    "document_source": str(ensure_index().source_path) if ensure_index().source_path else None,
                    "page_count": len(ensure_index().records),
                    "document_count": ensure_index().document_count,
                    "signature": ensure_index().signature,
                }
            )
            return

        if path == "/api/policies":
            index = ensure_index()
            docs = {}
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
            
            doc_list = list(docs.values())
            doc_list.sort(key=lambda d: (d["insurer"], d["product"]))
            self._send_json({"policies": doc_list})
            return

        if path in {"/", "/index.html"}:
            self._serve_static("index.html", "text/html; charset=utf-8")
            return

        if path == "/styles.css":
            self._serve_static("styles.css", "text/css; charset=utf-8")
            return

        if path == "/app.js":
            self._serve_static("app.js", "application/javascript; charset=utf-8")
            return

        self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/upload":
            try:
                content_type = self.headers.get("Content-Type", "")
                if not content_type.startswith("multipart/form-data"):
                    self._send_json({"error": "Content-Type must be multipart/form-data"}, status=HTTPStatus.BAD_REQUEST)
                    return
                
                # Extract boundary
                boundary = content_type.split("boundary=")[1].encode("utf-8")
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                
                # Parse body parts
                parts = body.split(b"--" + boundary)
                file_data = None
                filename = "uploaded_document.pdf"
                
                for part in parts:
                    if b"filename=" in part:
                        # Extract headers and content of the file part
                        headers_part, content_part = part.split(b"\r\n\r\n", 1)
                        content_part = content_part.rsplit(b"\r\n", 1)[0] # remove trailing \r\n
                        
                        # Find filename
                        fn_match = re.search(br'filename="([^"]+)"', headers_part)
                        if fn_match:
                            filename = fn_match.group(1).decode("utf-8", errors="ignore")
                        
                        file_data = content_part
                        break
                
                if not file_data:
                    self._send_json({"error": "No file found in request"}, status=HTTPStatus.BAD_REQUEST)
                    return
                
                # Ingest the PDF data in-memory!
                index = ensure_index()
                from .ingest import extract_records_from_pdf
                records = extract_records_from_pdf(file_data, filename, f"uploaded/{filename}")
                
                if not records:
                    self._send_json({"error": "Failed to extract text from PDF (it might be empty or encrypted)"}, status=HTTPStatus.BAD_REQUEST)
                    return
                
                # Add to index records in-memory
                index.records.extend(records)
                index.document_count = len({r.doc_id for r in index.records})
                
                # Re-calculate document frequency for terms
                for record in records:
                    for term in record.token_counts:
                        index.document_frequency[term] = index.document_frequency.get(term, 0) + 1
                
                self._send_json({
                    "success": True,
                    "filename": filename,
                    "page_count": len(records),
                    "total_pages": len(index.records),
                    "total_documents": index.document_count,
                })
            except Exception as e:
                self._send_json({"error": f"Upload processing failed: {str(e)}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if path == "/api/ask":
            try:
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(length).decode("utf-8")
                    payload = json.loads(raw or "{}")
                    query = str(payload.get("query", "")).strip()
                    file_name = payload.get("file_name")
                    session_id = str(payload.get("session_id") or "default").strip() or "default"
                    chat_history = payload.get("chat_history", [])
                    confirm_fallback = bool(payload.get("confirm_fallback", False))
                    if file_name:
                        file_name = str(file_name).strip()
                except Exception as exc:
                    self.send_error(HTTPStatus.BAD_REQUEST, f"Invalid JSON payload: {exc}")
                    return

                if not query:
                    self._send_json({"error": "Query is required"}, status=HTTPStatus.BAD_REQUEST)
                    return

                index = ensure_index()
                state = ensure_session_state(session_id)
                route = route_query(query)
                scope, scope_reasoning = classify_query_scope(query, file_name=file_name)
                allow_out_of_scope = allow_out_of_scope_answers()
                fallback_confirmation_required = require_fallback_confirmation()
                response_meta = {
                    "session_id": session_id,
                    "query_scope": scope,
                    "scope_reasoning": scope_reasoning,
                    "assistant_mode": "insurance_rag",
                    "requires_fallback_confirmation": False,
                    "session_state": state.status,
                }

                if scope == "out_of_scope" and (state.status == "fallback_confirmed" or confirm_fallback or is_confirmation_query(query)):
                    query_to_answer = state.last_out_of_scope_query or query
                    state.status = "fallback_confirmed"
                    state.last_out_of_scope_query = None
                    result = answer_query(index, query_to_answer, file_name=file_name, mode="fallback_confirmed", chat_history=chat_history)
                    response_meta.update(
                        {
                            "assistant_mode": "fallback_confirmed",
                            "requires_fallback_confirmation": False,
                            "session_state": state.status,
                        }
                    )
                elif scope == "out_of_scope" and not allow_out_of_scope:
                    state.status = "insurance"
                    state.last_out_of_scope_query = None
                    result = QueryResult(
                        answer=OUT_OF_SCOPE_REFUSAL_MESSAGE,
                        confidence=0.0,
                        route=route,
                        sources=[],
                        trace=["server: refused out-of-scope query before generation"],
                    )
                    response_meta.update(
                        {
                            "assistant_mode": "insurance_rag",
                            "requires_fallback_confirmation": False,
                            "session_state": state.status,
                        }
                    )
                elif scope == "out_of_scope" and fallback_confirmation_required and state.status != "fallback_confirmed":
                    state.status = "awaiting_confirmation"
                    state.last_out_of_scope_query = query
                    from .agent import INTERNET_SEARCH_PROMPT_MESSAGE, translate_to_user_language
                    result = QueryResult(
                        answer=translate_to_user_language(INTERNET_SEARCH_PROMPT_MESSAGE, query),
                        confidence=0.0,
                        route=route,
                        sources=[],
                        trace=["server: awaiting fallback confirmation for out-of-scope query"],
                    )
                    response_meta.update(
                        {
                            "assistant_mode": "insurance_rag",
                            "requires_fallback_confirmation": True,
                            "session_state": state.status,
                        }
                    )
                else:
                    state.status = "insurance"
                    state.last_out_of_scope_query = None
                    result = answer_query(index, query, file_name=file_name, mode="insurance_rag", chat_history=chat_history)
                    
                    # If the LLM or fallback synthesizer triggered the internet search prompt, we must await confirmation
                    requires_fallback = any("insufficient retrieved context" in t or "NO_CONTEXT tag" in t for t in result.trace)
                    
                    if requires_fallback:
                        state.status = "awaiting_confirmation"
                        state.last_out_of_scope_query = query
                    
                    response_meta.update(
                        {
                            "assistant_mode": "insurance_rag",
                            "requires_fallback_confirmation": requires_fallback,
                            "session_state": state.status,
                        }
                    )

                self._send_json(
                    {
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
                        **response_meta,
                    }
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._send_json({"error": f"An internal server error occurred while processing the query. Details: {e}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def _serve_static(self, relative_path: str, content_type: str) -> None:
        file_path = WEB_DIR / relative_path
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Static asset not found")
            return

        payload = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
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


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    print("PolicyLens AI server starting up...", flush=True)
    print("Index will be loaded lazily on the first request.", flush=True)

    server = ThreadingHTTPServer((host, port), PolicyLensHandler)
    print(f"Open http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()

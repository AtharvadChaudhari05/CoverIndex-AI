from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from .config import CACHE_DIR, default_source_candidates
from .models import CachedIndex, PageRecord
from .utils import choose_title_from_text, normalize_text, token_counts


SOURCE_INSURERS = {
    "hdfc": "HDFC Life",
    "sbi": "SBI General",
    "tata aig": "Tata AIG",
    "lic": "LIC",
    "aegon": "Aegon Life",
    "icici": "ICICI Prudential",
}


DOCUMENT_TYPES = [
    ("customer information sheet", "Customer Information Sheet"),
    ("policy bond", "Policy Bond"),
    ("policy wording", "Policy Wording"),
    ("policy document", "Policy Document"),
    ("brochure", "Brochure"),
    ("benefit illustration", "Benefit Illustration"),
]


def resolve_source_path() -> Path | None:
    for candidate in default_source_candidates():
        if candidate.exists():
            return candidate
    return None


def source_signature(source: Path) -> str:
    hasher = hashlib.sha1()
    if source.is_dir():
        for path in sorted(source.rglob("*")):
            if path.is_file():
                stat = path.stat()
                hasher.update(str(path.relative_to(source)).replace("\\", "/").encode("utf-8"))
                hasher.update(str(stat.st_size).encode("utf-8"))
    else:
        stat = source.stat()
        hasher.update(str(source.name).encode("utf-8"))
        hasher.update(str(stat.st_size).encode("utf-8"))
    return hasher.hexdigest()


def load_cached_index(signature: str | None) -> CachedIndex | None:
    # Support both gzip (.json.gz) and legacy plain JSON (.json)
    gz_file = CACHE_DIR / "page_index.json.gz"
    plain_file = CACHE_DIR / "page_index.json"
    cache_file = gz_file if gz_file.exists() else (plain_file if plain_file.exists() else None)
    if cache_file is None:
        return None
    try:
        if cache_file.suffix == ".gz":
            raw = gzip.decompress(cache_file.read_bytes()).decode("utf-8")
        else:
            raw = cache_file.read_text(encoding="utf-8")
        payload = json.loads(raw)
        cached = CachedIndex.from_json(payload)
        if signature is None or cached.signature == signature:
            return cached
    except Exception:
        return None
    return None


def save_cached_index(index: CachedIndex) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = CACHE_DIR / "page_index.json.gz"
        raw = json.dumps(index.to_json(), ensure_ascii=True).encode("utf-8")
        cache_file.write_bytes(gzip.compress(raw, compresslevel=6))
        # Remove old plain JSON if it exists
        old_plain = CACHE_DIR / "page_index.json"
        if old_plain.exists():
            old_plain.unlink(missing_ok=True)
    except OSError as e:
        print(f"[InsureIndex AI] Warning: Could not write cache file (Read-only filesystem): {e}")


def build_page_index(source: Path | None = None) -> tuple[list[PageRecord], str, Path | None]:
    source_path = source or resolve_source_path()
    
    # AGGRESSIVE CACHE LOADING: Always use cache if available in production to prevent OOM
    cached = load_cached_index(None) # None signature means skip check
    if cached is not None and len(cached.records) > 0:
        print("[PolicyLens AI] Loaded aggressively from cache! Skipping file hashing.", flush=True)
        return cached.records, cached.signature, source_path

    if source_path is None:
        return [], "no-source", None

    signature = source_signature(source_path)
    records: list[PageRecord] = []
    if source_path.is_dir():
        pdf_paths = sorted(path for path in source_path.rglob("*.pdf") if path.is_file())
        total = len(pdf_paths)
        print(f"[InsureIndex AI] Found {total} PDF files. Building page index...")
        for idx, pdf_path in enumerate(pdf_paths, 1):
            print(f"[InsureIndex AI] [{idx}/{total}] Extracting {pdf_path.name}...")
            records.extend(extract_records_from_pdf(pdf_path.read_bytes(), pdf_path.name, str(pdf_path)))
    elif source_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(source_path) as archive:
            members = [m for m in archive.namelist() if m.lower().endswith(".pdf") and not m.endswith("/")]
            total = len(members)
            print(f"[InsureIndex AI] Found {total} PDF files in zip. Building page index...")
            for idx, member in enumerate(members, 1):
                print(f"[InsureIndex AI] [{idx}/{total}] Extracting zip member {Path(member).name}...")
                records.extend(
                    extract_records_from_pdf(archive.read(member), Path(member).name, f"{source_path}!{member}")
                )
    elif source_path.suffix.lower() == ".pdf":
        print(f"[InsureIndex AI] Indexing single PDF: {source_path.name}...")
        records.extend(extract_records_from_pdf(source_path.read_bytes(), source_path.name, str(source_path)))

    save_cached_index(CachedIndex(signature=signature, records=records, document_count=len({r.doc_id for r in records})))
    return records, signature, source_path


def extract_records_from_pdf(data: bytes, file_name: str, source_path: str) -> list[PageRecord]:
    reader = PdfReader(io.BytesIO(data))
    source_name = Path(file_name).name
    base_title = title_from_filename(source_name)
    insurer = infer_insurer(source_name)
    product = infer_product(source_name)
    document_type = infer_document_type(source_name)
    doc_id = hashlib.sha1(source_path.encode("utf-8")).hexdigest()[:16]

    records: list[PageRecord] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        if not text:
            continue
        # Cap text per page to limit memory/cache size; 3000 chars is ample for LLM context
        if len(text) > 3000:
            text = text[:3000]

        title = choose_title_from_text(text, base_title)
        if page_number == 1 and title:
            product = infer_product(title) or product
            insurer = infer_insurer(title) or insurer
            document_type = infer_document_type(title) or document_type

        records.append(
            PageRecord(
                doc_id=doc_id,
                source_name=source_name,
                source_path=source_path,
                file_name=file_name,
                insurer=insurer,
                product=product,
                document_type=document_type,
                page_number=page_number,
                title=title,
                text=text,
                token_counts=dict(token_counts(text)),
                token_count=len(text.split()),
            )
        )
    return records


def title_from_filename(file_name: str) -> str:
    stem = Path(file_name).stem
    cleaned = re.sub(r"[_-]+", " ", stem)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or file_name


def infer_insurer(text: str) -> str:
    lowered = text.lower()
    for needle, name in SOURCE_INSURERS.items():
        if needle in lowered:
            return name
    return "Unknown Insurer"


def infer_product(text: str) -> str:
    stem = Path(text).stem if "." in text else text
    cleaned = re.sub(r"(?i)\b(policy document|policy bond|policy wording|customer information sheet|brochure|appendix)\b", "", stem)
    cleaned = re.sub(r"(?i)\b(v\d+|uin\s*[-–]?\s*[\w-]+)\b", "", cleaned)
    cleaned = re.sub(r"[_-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    return cleaned or "Policy"


def infer_document_type(text: str) -> str:
    lowered = text.lower()
    for needle, label in DOCUMENT_TYPES:
        if needle in lowered:
            return label
    return "Policy Document"

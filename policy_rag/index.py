from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .ingest import build_page_index
from .models import PageRecord, SearchHit
from .utils import compact_whitespace, normalize_text, split_sentences, tokenize


@dataclass(slots=True)
class PageIndex:
    records: list[PageRecord]
    signature: str
    source_path: Path | None
    document_count: int
    avg_doc_length: float
    document_frequency: dict[str, int]

    @classmethod
    def load(cls, source: Path | None = None) -> "PageIndex":
        records, signature, source_path = build_page_index(source)
        doc_freq: dict[str, int] = defaultdict(int)
        total_length = 0
        for record in records:
            total_length += record.token_count
            for term in record.token_counts:
                doc_freq[term] += 1
        avg_doc_length = total_length / max(len(records), 1)
        return cls(
            records=records,
            signature=signature,
            source_path=source_path,
            document_count=len({record.doc_id for record in records}),
            avg_doc_length=avg_doc_length if avg_doc_length > 0 else 1.0,
            document_frequency=dict(doc_freq),
        )

    def search(
        self,
        query: str,
        *,
        insurer_filter: str | None = None,
        product_hint: str | None = None,
        file_name_filter: str | None = None,
        top_k: int = 5,
    ) -> list[SearchHit]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        query_counter = Counter(query_tokens)
        hits: list[SearchHit] = []

        for record in self.records:
            if file_name_filter:
                if record.file_name.lower() != file_name_filter.lower():
                    continue
            else:
                if insurer_filter and insurer_filter.lower() not in record.insurer.lower():
                    continue



            score = self._bm25(record, query_counter)
            score += self._metadata_boost(record, query, product_hint)

            if score <= 0:
                continue

            sentence = self._best_sentence(record.text, query_tokens)
            hits.append(SearchHit(record=record, score=score, highlight=sentence))

        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]

    def expanded_context(self, hits: list[SearchHit], max_pages: int = 6) -> list[SearchHit]:
        expanded: list[SearchHit] = []
        seen: set[tuple[str, int]] = set()
        
        # Pass 1: Add all direct hits first
        for hit in hits:
            key = (hit.record.doc_id, hit.record.page_number)
            if key not in seen:
                expanded.append(hit)
                seen.add(key)
            if len(expanded) >= max_pages:
                return expanded
                
        # Pass 2: Add neighbor pages if there is still space
        for hit in hits:
            if len(expanded) >= max_pages:
                break
            for delta in (-1, 1):
                neighbor = self._neighbor_page(hit.record, delta)
                if neighbor is None:
                    continue
                key = (neighbor.doc_id, neighbor.page_number)
                if key in seen:
                    continue
                seen.add(key)
                neighbor_score = max(hit.score - 1.3, 0.1)
                expanded.append(
                    SearchHit(
                        record=neighbor,
                        score=neighbor_score,
                        highlight=self._best_sentence(neighbor.text, tokenize(hit.highlight)),
                    )
                )
                if len(expanded) >= max_pages:
                    return expanded
        return expanded

    def _neighbor_page(self, record: PageRecord, delta: int) -> PageRecord | None:
        for candidate in self.records:
            if candidate.doc_id == record.doc_id and candidate.page_number == record.page_number + delta:
                return candidate
        return None

    def _bm25(self, record: PageRecord, query_counter: Counter[str]) -> float:
        k1 = 1.5
        b = 0.75
        score = 0.0
        doc_len = max(record.token_count, 1)

        for term, query_tf in query_counter.items():
            tf = record.token_counts.get(term, 0)
            if not tf:
                continue

            doc_freq = self.document_frequency.get(term, 0)
            idf = math.log(1 + (len(self.records) - doc_freq + 0.5) / (doc_freq + 0.5))
            denom = tf + k1 * (1 - b + b * (doc_len / self.avg_doc_length))
            score += idf * ((tf * (k1 + 1)) / denom) * (1 + math.log1p(query_tf))

        return score

    def _metadata_boost(self, record: PageRecord, query: str, product_hint: str | None) -> float:
        lowered = query.lower()
        boost = 0.0

        if record.insurer != "Unknown Insurer" and record.insurer.lower() in lowered:
            boost += 4.0

        if "hdfc" in lowered and "hdfc" in record.insurer.lower():
            boost += 3.0

        if product_hint:
            record_blob = f"{record.title} {record.product} {record.file_name}".lower()
            hint_tokens = tokenize(product_hint)
            if hint_tokens and any(token in record_blob for token in hint_tokens):
                boost += 3.0

        file_blob = f"{record.title} {record.product} {record.file_name}".lower()
        if "policy bond" in lowered and "policy bond" in file_blob:
            boost += 1.2
        if "policy wording" in lowered and "policy wording" in file_blob:
            boost += 1.2
        if "benefit" in lowered and any(term in file_blob for term in ["benefit", "coverage", "sum assured"]):
            boost += 0.9

        title_blob = record.title.lower()
        for term in tokenize(query):
            if term in title_blob:
                boost += 0.45

        return boost

    def _best_sentence(self, text: str, query_tokens: list[str]) -> str:
        sentences = split_sentences(text)
        if not sentences:
            return compact_whitespace(text)

        best_sentence = sentences[0]
        best_score = -1.0
        query_set = set(query_tokens)

        for sentence in sentences[:12]:
            tokens = tokenize(sentence)
            if not tokens:
                continue
            overlap = len(query_set.intersection(tokens))
            keyword_hits = sum(1 for token in tokens if token in {"premium", "benefit", "claim", "exclusion", "eligibility", "nominee", "sum", "assured", "coverage", "maturity"})
            score = overlap * 2.0 + keyword_hits * 0.3 + min(len(sentence) / 120.0, 1.0) * 0.2
            if score > best_score:
                best_score = score
                best_sentence = sentence

        return compact_whitespace(best_sentence, 320)

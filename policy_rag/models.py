from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PageRecord:
    doc_id: str
    source_name: str
    source_path: str
    file_name: str
    insurer: str
    product: str
    document_type: str
    page_number: int
    title: str
    text: str
    token_counts: dict[str, int]
    token_count: int

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "PageRecord":
        return cls(**payload)


@dataclass(slots=True)
class SearchHit:
    record: PageRecord
    score: float
    highlight: str


@dataclass(slots=True)
class QueryRoute:
    insurer: str | None
    product_hint: str | None
    intent: str
    reasoning: str


@dataclass(slots=True)
class QueryResult:
    answer: str
    confidence: float
    route: QueryRoute
    sources: list[dict[str, Any]]
    trace: list[str]


@dataclass(slots=True)
class CachedIndex:
    signature: str
    records: list[PageRecord]
    document_count: int

    def to_json(self) -> dict[str, Any]:
        return {
            "signature": self.signature,
            "document_count": self.document_count,
            "records": [record.to_json() for record in self.records],
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "CachedIndex":
        return cls(
            signature=payload["signature"],
            document_count=payload["document_count"],
            records=[PageRecord.from_json(item) for item in payload["records"]],
        )

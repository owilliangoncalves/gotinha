from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class ProcessingStatus(StrEnum):
    PROCESSING = "processando"
    PROCESSED = "processado"
    NEEDS_OCR = "precisa_ocr"
    FAILED = "falha"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ChunkRecord:
    id: str
    document_id: str
    document_name: str
    page: int
    section: str | None
    text: str


@dataclass(slots=True)
class DocumentRecord:
    id: str
    filename: str
    title: str
    sha256: str
    source_path: str | None = None
    origin: str = "upload"
    uploaded_at: datetime = field(default_factory=utc_now)
    status: ProcessingStatus = ProcessingStatus.PROCESSING
    total_pages: int = 0
    total_chunks: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SourceRecord:
    chunk_id: str
    document_id: str
    document_name: str
    page: int
    section: str | None
    text: str
    score: float


@dataclass(slots=True)
class ConsultationRecord:
    id: str
    question: str
    answer: str
    asked_at: datetime = field(default_factory=utc_now)
    sufficient_evidence: bool = False
    sources: list[SourceRecord] = field(default_factory=list)

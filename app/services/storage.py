from __future__ import annotations

from dataclasses import replace
from threading import RLock

from app.models.domain import ChunkRecord, ConsultationRecord, DocumentRecord


class InMemoryKnowledgeBase:
    """Simple in-memory store used as the first runnable implementation."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._documents: dict[str, DocumentRecord] = {}
        self._chunks: dict[str, list[ChunkRecord]] = {}
        self._consultations: list[ConsultationRecord] = []

    def save_document(self, document: DocumentRecord) -> DocumentRecord:
        with self._lock:
            stored = replace(document)
            self._documents[stored.id] = stored
            self._chunks.setdefault(stored.id, [])
            return replace(stored)

    def find_document_by_hash(self, sha256: str) -> DocumentRecord | None:
        with self._lock:
            for document in self._documents.values():
                if document.sha256 == sha256:
                    return replace(document)
        return None

    def set_document_chunks(self, document_id: str, chunks: list[ChunkRecord]) -> None:
        with self._lock:
            self._chunks[document_id] = list(chunks)

    def update_document(self, document: DocumentRecord) -> DocumentRecord:
        return self.save_document(document)

    def get_document(self, document_id: str) -> DocumentRecord | None:
        with self._lock:
            document = self._documents.get(document_id)
            return replace(document) if document else None

    def list_documents(self) -> list[DocumentRecord]:
        with self._lock:
            documents = [replace(document) for document in self._documents.values()]
        return sorted(documents, key=lambda item: item.uploaded_at, reverse=True)

    def get_chunks(self, document_id: str) -> list[ChunkRecord]:
        with self._lock:
            return list(self._chunks.get(document_id, []))

    def all_chunks(self, document_ids: list[str] | None = None) -> list[ChunkRecord]:
        with self._lock:
            if document_ids:
                selected_ids = set(document_ids)
                return [
                    chunk
                    for document_id, chunks in self._chunks.items()
                    if document_id in selected_ids
                    for chunk in chunks
                ]
            return [chunk for chunks in self._chunks.values() for chunk in chunks]

    def save_consultation(self, consultation: ConsultationRecord) -> ConsultationRecord:
        with self._lock:
            stored = replace(consultation, sources=list(consultation.sources))
            self._consultations.append(stored)
            return replace(stored, sources=list(stored.sources))

    def list_consultations(self) -> list[ConsultationRecord]:
        with self._lock:
            consultations = [
                replace(consultation, sources=list(consultation.sources))
                for consultation in self._consultations
            ]
        return sorted(consultations, key=lambda item: item.asked_at, reverse=True)

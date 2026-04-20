from __future__ import annotations

from pathlib import Path

from app.models.domain import DocumentRecord
from app.services.pdf_processing.ingestion import PDFIngestionService


class DocumentLibraryService:
    def __init__(self, ingestion_service: PDFIngestionService, documents_dir: str) -> None:
        self.ingestion_service = ingestion_service
        self.documents_dir = Path(documents_dir)

    def sync(self) -> tuple[list[DocumentRecord], list[str]]:
        if not self.documents_dir.exists():
            return [], [f"Diretorio de documentos nao encontrado: {self.documents_dir}"]

        documents: list[DocumentRecord] = []
        warnings: list[str] = []
        for pdf_path in sorted(self.documents_dir.rglob("*.pdf")):
            try:
                documents.append(self.ingestion_service.ingest_path(pdf_path))
            except Exception as exc:  # pragma: no cover - protective branch
                warnings.append(f"Falha ao processar {pdf_path.name}: {exc}")
        return documents, warnings

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import uuid4

import fitz

from app.models.domain import ChunkRecord, DocumentRecord, ProcessingStatus
from app.services.storage import InMemoryKnowledgeBase


class PDFIngestionError(ValueError):
    """Raised when a document cannot be parsed safely."""


class PDFIngestionService:
    def __init__(
        self,
        store: InMemoryKnowledgeBase,
        *,
        chunk_size: int = 900,
        chunk_overlap: int = 120,
    ) -> None:
        self.store = store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def ingest(self, filename: str, content: bytes) -> DocumentRecord:
        return self._ingest(
            filename=filename,
            content=content,
            source_path=None,
            origin="upload",
        )

    def ingest_path(self, path: str | Path) -> DocumentRecord:
        pdf_path = Path(path)
        return self._ingest(
            filename=pdf_path.name,
            content=pdf_path.read_bytes(),
            source_path=str(pdf_path.resolve()),
            origin="filesystem",
        )

    def _ingest(
        self,
        *,
        filename: str,
        content: bytes,
        source_path: str | None,
        origin: str,
    ) -> DocumentRecord:
        if not filename.lower().endswith(".pdf"):
            raise PDFIngestionError("Apenas arquivos PDF sao aceitos.")
        if not content:
            raise PDFIngestionError("O arquivo enviado esta vazio.")

        document_hash = hashlib.sha256(content).hexdigest()
        existing = self.store.find_document_by_hash(document_hash)
        if existing:
            return existing

        document_id = str(uuid4())
        title = Path(filename).stem.replace("_", " ").strip() or "Documento sem titulo"

        record = DocumentRecord(
            id=document_id,
            filename=filename,
            title=title,
            sha256=document_hash,
            source_path=source_path,
            origin=origin,
            status=ProcessingStatus.PROCESSING,
        )
        self.store.save_document(record)

        try:
            pdf = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:  # pragma: no cover - defensive branch
            failed = DocumentRecord(
                id=record.id,
                filename=record.filename,
                title=record.title,
                sha256=record.sha256,
                source_path=record.source_path,
                origin=record.origin,
                uploaded_at=record.uploaded_at,
                status=ProcessingStatus.FAILED,
                warnings=["Nao foi possivel abrir o PDF enviado."],
            )
            self.store.update_document(failed)
            raise PDFIngestionError("Nao foi possivel ler o PDF enviado.") from exc

        chunks: list[ChunkRecord] = []
        warnings: list[str] = []
        text_pages = 0

        with pdf:
            total_pages = pdf.page_count
            for page_index, page in enumerate(pdf, start=1):
                raw_text = page.get_text("text") or ""
                cleaned_text = self._clean_text(raw_text)
                if not cleaned_text:
                    warnings.append(
                        f"Pagina {page_index} sem texto extraivel. OCR sera necessario em uma etapa futura."
                    )
                    continue

                text_pages += 1
                section = self._infer_section(cleaned_text)
                for chunk_text in self._chunk_text(cleaned_text):
                    chunks.append(
                        ChunkRecord(
                            id=str(uuid4()),
                            document_id=document_id,
                            document_name=filename,
                            page=page_index,
                            section=section,
                            text=chunk_text,
                        )
                    )

        status = ProcessingStatus.PROCESSED if text_pages else ProcessingStatus.NEEDS_OCR
        finished = DocumentRecord(
            id=record.id,
            filename=record.filename,
            title=record.title,
            sha256=record.sha256,
            source_path=record.source_path,
            origin=record.origin,
            uploaded_at=record.uploaded_at,
            status=status,
            total_pages=total_pages,
            total_chunks=len(chunks),
            warnings=warnings,
        )
        self.store.set_document_chunks(document_id, chunks)
        return self.store.update_document(finished)

    def _clean_text(self, text: str) -> str:
        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _infer_section(self, text: str) -> str | None:
        lines = [line.strip(" :-") for line in text.splitlines() if line.strip()]
        for line in lines[:5]:
            if 4 <= len(line) <= 120 and (line.isupper() or line == line.title()):
                return line
        return lines[0] if lines else None

    def _chunk_text(self, text: str) -> list[str]:
        paragraphs = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
        if not paragraphs:
            return []

        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}" if current else paragraph
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current.strip())
                current = self._seed_with_overlap(current, paragraph)
                if len(current) <= self.chunk_size:
                    continue

            long_parts = self._split_long_block(paragraph)
            chunks.extend(long_parts[:-1])
            current = long_parts[-1] if long_parts else ""

        if current:
            chunks.append(current.strip())

        return chunks

    def _seed_with_overlap(self, current: str, next_paragraph: str) -> str:
        overlap = current[-self.chunk_overlap :].strip()
        if overlap:
            return f"{overlap}\n\n{next_paragraph}".strip()
        return next_paragraph

    def _split_long_block(self, block: str) -> list[str]:
        words = block.split()
        if not words:
            return []

        pieces: list[str] = []
        current_words: list[str] = []
        for word in words:
            candidate = " ".join([*current_words, word]).strip()
            if candidate and len(candidate) <= self.chunk_size:
                current_words.append(word)
                continue

            if current_words:
                pieces.append(" ".join(current_words))
                overlap_words = " ".join(current_words)[-self.chunk_overlap :].strip().split()
                current_words = overlap_words + [word]
            else:
                pieces.append(word[: self.chunk_size])
                remainder = word[self.chunk_size :].strip()
                current_words = [remainder] if remainder else []

        if current_words:
            pieces.append(" ".join(current_words))
        return [piece.strip() for piece in pieces if piece.strip()]

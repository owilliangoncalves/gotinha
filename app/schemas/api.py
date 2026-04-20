from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain import ConsultationRecord, DocumentRecord, SourceRecord


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class DocumentResponse(BaseModel):
    id: str
    nome_arquivo: str
    titulo: str
    hash_arquivo: str
    origem: str
    caminho_origem: str | None
    status: str
    paginas: int
    total_chunks: int
    avisos: list[str]
    data_upload: datetime

    @classmethod
    def from_record(cls, record: DocumentRecord) -> "DocumentResponse":
        return cls(
            id=record.id,
            nome_arquivo=record.filename,
            titulo=record.title,
            hash_arquivo=record.sha256,
            origem=record.origin,
            caminho_origem=record.source_path,
            status=record.status.value,
            paginas=record.total_pages,
            total_chunks=record.total_chunks,
            avisos=record.warnings,
            data_upload=record.uploaded_at,
        )


class DocumentSyncResponse(BaseModel):
    total_documentos_sincronizados: int
    documentos: list[DocumentResponse]
    avisos: list[str]


class SourceResponse(BaseModel):
    chunk_id: str
    documento: str
    pagina: int
    secao: str | None
    trecho: str
    score_relevancia: float

    @classmethod
    def from_record(cls, record: SourceRecord) -> "SourceResponse":
        return cls(
            chunk_id=record.chunk_id,
            documento=record.document_name,
            pagina=record.page,
            secao=record.section,
            trecho=record.text,
            score_relevancia=record.score,
        )


class QueryRequest(BaseModel):
    pergunta: str = Field(min_length=3)
    documentos_ids: list[str] | None = None
    top_k: int | None = Field(default=None, ge=1, le=8)


class QueryResponse(BaseModel):
    resposta: str
    suficiente: bool
    fontes: list[SourceResponse]


class ConsultationResponse(BaseModel):
    id: str
    pergunta: str
    resposta: str
    suficiente: bool
    data_consulta: datetime
    fontes: list[SourceResponse]

    @classmethod
    def from_record(cls, record: ConsultationRecord) -> "ConsultationResponse":
        return cls(
            id=record.id,
            pergunta=record.question,
            resposta=record.answer,
            suficiente=record.sufficient_evidence,
            data_consulta=record.asked_at,
            fontes=[SourceResponse.from_record(source) for source in record.sources],
        )

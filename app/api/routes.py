from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_container
from app.core.settings import Settings, get_settings
from app.models.domain import ConsultationRecord
from app.schemas.api import (
    ConsultationResponse,
    DocumentResponse,
    DocumentSyncResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SourceResponse,
)
from app.services.container import ServiceContainer
from app.services.pdf_processing.ingestion import PDFIngestionError

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def healthcheck(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    container: ServiceContainer = Depends(get_container),
) -> DocumentResponse:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF sao aceitos.")

    try:
        content = await file.read()
        document = container.ingestion_service.ingest(filename, content)
    except PDFIngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DocumentResponse.from_record(document)


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(
    container: ServiceContainer = Depends(get_container),
) -> list[DocumentResponse]:
    return [
        DocumentResponse.from_record(document)
        for document in container.store.list_documents()
    ]


@router.post("/documents/sync", response_model=DocumentSyncResponse)
def sync_documents(
    container: ServiceContainer = Depends(get_container),
) -> DocumentSyncResponse:
    documents, warnings = container.library_service.sync()
    return DocumentSyncResponse(
        total_documentos_sincronizados=len(documents),
        documentos=[DocumentResponse.from_record(document) for document in documents],
        avisos=warnings,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    container: ServiceContainer = Depends(get_container),
) -> DocumentResponse:
    document = container.store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado.")
    return DocumentResponse.from_record(document)


@router.post("/consultas", response_model=QueryResponse)
def query_documents(
    payload: QueryRequest,
    container: ServiceContainer = Depends(get_container),
) -> QueryResponse:
    sources = container.retrieval_service.search(
        payload.pergunta,
        top_k=payload.top_k,
        document_ids=payload.documentos_ids,
    )
    answer:str, sufficient: tuple[str, bool] = container.answer_service.compose(payload.pergunta, sources)

    consultation = ConsultationRecord(
        id=str(object= uuid4()),
        question=payload.pergunta,
        answer=answer,
        sufficient_evidence=sufficient,
        sources=sources,
    )
    container.store.save_consultation(consultation)

    return QueryResponse(
        resposta=answer,
        suficiente=sufficient,
        fontes=[SourceResponse.from_record(source) for source in sources],
    )


@router.get("/consultas", response_model=list[ConsultationResponse])
def list_consultations(
    container: ServiceContainer = Depends(get_container),
) -> list[ConsultationResponse]:
    return [
        ConsultationResponse.from_record(consultation)
        for consultation in container.store.list_consultations()
    ]

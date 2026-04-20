from fastapi import FastAPI

from app.api.routes import router
from app.models.settings import Settings, get_settings
from app.services.container import ServiceContainer
from app.services.llm.groq_client import GroqChatClient
from app.services.llm.service import EvidenceAnswerService
from app.services.pdf_processing.ingestion import PDFIngestionService
from app.services.pdf_processing.library import DocumentLibraryService
from app.services.retrieval.service import RetrievalService
from app.services.storage import InMemoryKnowledgeBase
from app.web import router as web_router


def build_services(settings: Settings | None = None) -> ServiceContainer:
    settings = settings or get_settings()
    store = InMemoryKnowledgeBase()
    ingestion_service = PDFIngestionService(
        store,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    library_service = DocumentLibraryService(ingestion_service, settings.documents_dir)

    groq_client = None
    if settings.groq_api_key:
        groq_client = GroqChatClient.from_settings(settings)

    services = ServiceContainer(
        store=store,
        ingestion_service=ingestion_service,
        library_service=library_service,
        retrieval_service=RetrievalService(
            store,
            default_top_k=settings.default_top_k,
            min_relevance_score=settings.min_relevance_score,
            min_overlap_terms=settings.min_overlap_terms,
        ),
        answer_service=EvidenceAnswerService(groq_client=groq_client),
    )
    if settings.auto_ingest_on_startup:
        library_service.sync()
    return services


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend inicial do buscador documental em saude com respostas rastreaveis."
        ),
    )
    application.state.services = build_services(settings)
    application.include_router(web_router)
    application.include_router(router)
    return application


app = create_app()

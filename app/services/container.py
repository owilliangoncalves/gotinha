from dataclasses import dataclass

from app.services.llm.service import EvidenceAnswerService
from app.services.pdf_processing.ingestion import PDFIngestionService
from app.services.pdf_processing.library import DocumentLibraryService
from app.services.retrieval.service import RetrievalService
from app.services.storage import InMemoryKnowledgeBase


@dataclass(slots=True)
class ServiceContainer:
    store: InMemoryKnowledgeBase
    ingestion_service: PDFIngestionService
    library_service: DocumentLibraryService
    retrieval_service: RetrievalService
    answer_service: EvidenceAnswerService

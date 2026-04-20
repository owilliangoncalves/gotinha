from __future__ import annotations

import re
import unicodedata

from app.models.domain import SourceRecord
from app.services.llm.groq_client import GroqChatClient, GroqClientError


class EvidenceAnswerService:
    """Builds an answer strictly from retrieved evidence without inventing new facts."""

    def __init__(self, groq_client: GroqChatClient | None = None) -> None:
        self.groq_client = groq_client

    def compose(self, question: str, sources: list[SourceRecord]) -> tuple[str, bool]:
        if not sources:
            return (
                "Nao encontrei evidencia documental suficiente para responder com segurança com a base atualmente processada.",
                False,
            )

        if self.groq_client:
            try:
                return self._compose_with_groq(question, sources)
            except GroqClientError:
                pass

        return self._compose_with_fallback(question, sources)

    def _compose_with_groq(
        self, question: str, sources: list[SourceRecord]
    ) -> tuple[str, bool]:
        system_prompt = (
            "Você responde perguntas sobre documentos de saúde. "
            "Use apenas as evidencias fornecidas, sem conhecimento externo. "
            "Nunca preencha lacunas com inferencias clínicas ou memória do modelo. "
            "Se a evidencia não for suficiente, estiver ambígua ou conflitar, diga isso claramente. "
            'Retorne apenas JSON valido com as chaves "resposta" e "suficiente".'
        )
        rendered_sources = []
        for index, source in enumerate(sources, start=1):
            rendered_sources.append(
                "\n".join(
                    [
                        f"Fonte {index}",
                        f"Documento: {source.document_name}",
                        f"Pagina: {source.page}",
                        f"Seção: {source.section or 'Não identificada'}",
                        f"Trecho: {source.text}",
                    ]
                )
            )
        sources_text = "\n\n".join(rendered_sources)

        user_prompt = (
            f"Pergunta: {question}\n\n"
            "Evidencias documentais:\n"
            f"{sources_text}\n\n"
            "Responda em português do Brasil de forma objetiva."
        )
        payload = self.groq_client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        answer = str(payload.get("resposta", "")).strip()
        sufficient = bool(payload.get("suficiente"))
        if not answer:
            raise GroqClientError("O modelo nao retornou uma resposta utilizável.")
        return answer, sufficient

    def _compose_with_fallback(
        self, question: str, sources: list[SourceRecord]
    ) -> tuple[str, bool]:
        terms = self._tokenize(question)
        candidates: list[tuple[float, str]] = []
        seen_sentences: set[str] = set()

        for source in sources:
            for sentence in self._split_sentences(source.text):
                normalized_sentence = self._normalize(sentence)
                if not normalized_sentence or normalized_sentence in seen_sentences:
                    continue
                sentence_terms = self._tokenize(sentence)
                overlap = terms & sentence_terms
                if not overlap:
                    continue
                seen_sentences.add(normalized_sentence)
                coverage_score = len(overlap) / len(terms)
                density_score = sum(
                    normalized_sentence.count(term) for term in overlap
                ) / max(len(sentence_terms), 1)
                candidate_score = (
                    (source.score * 0.45)
                    + (coverage_score * 0.45)
                    + (min(density_score * 2, 1.0) * 0.10)
                )
                candidates.append((candidate_score, sentence.strip()))

        if not candidates:
            return (
                "Encontrei trechos relacionados, mas nao ha evidencia textual suficientemente direta para responder com segurança com a base atualmente processada.",
                False,
            )

        candidates.sort(key=lambda item: item[0], reverse=True)
        selected_sentences = [sentence for _, sentence in candidates[:3]]
        answer = " ".join(selected_sentences)
        answer = re.sub(r"\s+", " ", answer).strip()
        return answer, True

    def _split_sentences(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
        return [sentence for sentence in sentences if sentence.strip()]

    def _normalize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        without_accents = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        return re.sub(r"\s+", " ", without_accents).strip()

    def _tokenize(self, question: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]{3,}", self._normalize(question)))

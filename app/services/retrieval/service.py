from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.models.domain import ChunkRecord, SourceRecord
from app.services.storage import InMemoryKnowledgeBase

STOP_WORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "efeito",
    "efeitos",
    "fala",
    "impacto",
    "impactos",
    "importancia",
    "importante",
    "influencia",
    "influencias",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "ou",
    "papel",
    "papeis",
    "principal",
    "principais",
    "para",
    "por",
    "qual",
    "quais",
    "que",
    "relevancia",
    "seu",
    "seus",
    "significado",
    "sobre",
    "sua",
    "suas",
    "se",
    "ser",
    "tema",
    "temas",
    "trata",
    "tratar",
    "um",
    "uma",
    "beneficio",
    "beneficios",
}


@dataclass(slots=True)
class RetrievalResult:
    source: SourceRecord


class RetrievalService:
    def __init__(
        self,
        store: InMemoryKnowledgeBase,
        *,
        default_top_k: int = 8,
        min_relevance_score: float = 0.5,
        min_overlap_terms: int = 3,
    ) -> None:
        self.store = store
        self.default_top_k = default_top_k
        self.min_relevance_score = min_relevance_score
        self.min_overlap_terms = min_overlap_terms

    def search(
        self,
        question: str,
        *,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> list[SourceRecord]:
        query = self._normalize(question)
        terms = self._tokenize(query)
        if not query or not terms:
            return []

        scored: list[SourceRecord] = []
        for chunk in self.store.all_chunks(document_ids=document_ids):
            score = self._score_chunk(chunk, query, terms)
            if score < self.min_relevance_score:
                continue

            scored.append(
                SourceRecord(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page=chunk.page,
                    section=chunk.section,
                    text=chunk.text,
                    score=round(score, 4),
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        deduplicated = self._deduplicate(scored)
        return deduplicated[: top_k or self.default_top_k]

    def _score_chunk(self, chunk: ChunkRecord, query: str, terms: set[str]) -> float:
        searchable_haystack = self._normalize(self._build_searchable_text(chunk))
        chunk_terms = self._tokenize(searchable_haystack)
        if not chunk_terms:
            return 0.0

        overlap = terms & chunk_terms
        overlap_count = len(overlap)
        if overlap_count == 0:
            return 0.0

        coverage_score = overlap_count / len(terms)
        required_overlap = self._required_overlap_count(len(terms))
        if overlap_count < required_overlap and coverage_score < 0.6:
            return 0.0

        density = sum(searchable_haystack.count(term) for term in overlap) / max(
            len(chunk_terms), 1
        )
        phrase_score = self._phrase_match_score(query, searchable_haystack)
        sentence_focus_score = self._sentence_focus_score(chunk.text, terms)
        full_coverage_bonus = 0.12 if coverage_score >= 0.85 else 0.0
        section_bonus = (
            0.06
            if chunk.section
            and any(term in self._normalize(chunk.section) for term in overlap)
            else 0.0
        )
        score = (
            (coverage_score * 0.62)
            + (min(density * 3, 1.0) * 0.14)
            + (phrase_score * 0.18)
            + (sentence_focus_score * 0.12)
            + full_coverage_bonus
            + section_bonus
        )
        return min(score, 1.0)

    def _required_overlap_count(self, query_term_count: int) -> int:
        if query_term_count <= 2:
            return 1
        return min(self.min_overlap_terms, query_term_count)

    def _deduplicate(self, sources: list[SourceRecord]) -> list[SourceRecord]:
        unique: list[SourceRecord] = []
        seen: set[tuple[str, int, str]] = set()
        for source in sources:
            key = (source.document_id, source.page, source.text[:120])
            if key in seen:
                continue
            seen.add(key)
            unique.append(source)
        return unique

    def _normalize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        without_accents = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        return re.sub(r"\s+", " ", without_accents).strip()

    def _tokenize(self, value: str) -> set[str]:
        return {
            self._normalize_token(token)
            for token in re.findall(r"[a-z0-9]{3,}", value)
            if token not in STOP_WORDS
            and self._normalize_token(token) not in STOP_WORDS
        }

    def _phrase_match_score(self, query: str, haystack: str) -> float:
        phrases = self._query_phrases(query)
        if not phrases:
            return 0.0

        matches = sum(1 for phrase in phrases if phrase in haystack)
        return matches / len(phrases)

    def _query_phrases(self, query: str) -> list[str]:
        tokens = [
            self._normalize_token(token)
            for token in re.findall(r"[a-z0-9]{3,}", query)
            if token not in STOP_WORDS
            and self._normalize_token(token) not in STOP_WORDS
        ]
        phrases: list[str] = []

        for size in (2, 3):
            if len(tokens) < size:
                continue

            for index in range(len(tokens) - size + 1):
                window = tokens[index : index + size]
                if not any(token not in STOP_WORDS for token in window):
                    continue
                phrases.append(" ".join(window))

        return phrases

    def _build_searchable_text(self, chunk: ChunkRecord) -> str:
        parts: list[str] = []
        if chunk.section:
            parts.append(chunk.section)
        parts.append(chunk.text)
        return "\n".join(parts)

    def _normalize_token(self, token: str) -> str:
        if len(token) > 4 and token.endswith("s"):
            return token[:-1]
        return token

    def _sentence_focus_score(self, text: str, terms: set[str]) -> float:
        best_score = 0.0

        for sentence in self._split_sentences(text):
            sentence_terms = self._tokenize(self._normalize(sentence))
            if not sentence_terms:
                continue

            overlap_score = len(terms & sentence_terms) / len(terms)
            best_score = max(best_score, overlap_score)

        return best_score

    def _split_sentences(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
        return [sentence for sentence in sentences if sentence.strip()]

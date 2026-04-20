from __future__ import annotations

import json

import httpx

from app.models.settings import Settings


class GroqClientError(RuntimeError):
    """Raised when the Groq API cannot produce a valid structured answer."""


class GroqChatClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        temperature: float,
        base_url: str,
        timeout_seconds: float,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "GroqChatClient":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY nao configurada.")

        return cls(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=settings.groq_temperature,
            base_url=settings.groq_base_url,
            timeout_seconds=settings.groq_timeout_seconds,
        )

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        payload: dict[str, str | int | float | list[dict[str, str]]] = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GroqClientError("Falha ao consultar o modelo configurado.") from exc

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise GroqClientError("Resposta invalida recebida da Groq.") from exc

        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = (
                cleaned.removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise GroqClientError("O modelo nao retornou JSON valido.") from exc

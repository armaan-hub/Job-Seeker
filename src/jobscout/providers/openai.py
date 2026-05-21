"""OpenAI provider."""

import os
from typing import Any

from jobscout.providers.base import AIProvider, AIResponse, AIModel, ProviderType


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"), base_url)
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
        return self._client

    def complete(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        """Send completion request to GPT."""
        client = self._get_client()

        model = kwargs.pop("model", "gpt-4o")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs,
        )

        return AIResponse(
            content=response.choices[0].message.content,
            model=model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            raw_response=response.model_dump(),
        )

    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI

    @property
    def default_model(self) -> AIModel:
        return AIModel(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            max_tokens=4096,
        )
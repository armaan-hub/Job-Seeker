"""Anthropic Claude provider."""

import os
from typing import Any

from jobscout.providers.base import AIProvider, AIResponse, AIModel, ProviderType


class AnthropicProvider(AIProvider):
    """Anthropic Claude AI provider."""

    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"))
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
        return self._client

    def complete(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        """Send completion request to Claude."""
        client = self._get_client()

        model = kwargs.pop("model", "claude-sonnet-4-7")
        max_tokens = kwargs.pop("max_tokens", 4096)

        messages = [{"role": "user", "content": prompt}]
        if system:
            messages = [
                {"role": "system", "content": system},
                *messages,
            ]

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            **kwargs,
        )

        return AIResponse(
            content=response.content[0].text,
            model=model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw_response=response.model_dump(),
        )

    def provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC

    @property
    def default_model(self) -> AIModel:
        return AIModel(
            name="claude-sonnet-4-7",
            provider=ProviderType.ANTHROPIC,
            max_tokens=4096,
        )
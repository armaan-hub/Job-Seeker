"""OpenCode-compatible provider (OpenAI-compatible API)."""

import os
from typing import Any

from jobscout.providers.base import AIModel, AIProvider, AIResponse, ProviderType


class OpenCodeProvider(AIProvider):
    """OpenCode proxy provider (OpenAI-compatible interface)."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        super().__init__(
            api_key=api_key or os.getenv("OPENCODE_API_KEY", ""),
            base_url=base_url or os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen"),
        )
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Lazy-load the OpenAI-compatible client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError as err:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                ) from err
        return self._client

    def complete(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        """Send completion request through OpenCode proxy."""
        client = self._get_client()

        model = kwargs.pop("model", None)
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
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            raw_response=response.model_dump(),
        )

    def provider_type(self) -> ProviderType:
        return ProviderType.OPENCODE

    @property
    def default_model(self) -> AIModel:
        return AIModel(
            name="minimax-m2.7",
            provider=ProviderType.OPENCODE,
            max_tokens=4096,
        )

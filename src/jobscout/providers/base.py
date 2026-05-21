"""Base interface for AI providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProviderType(Enum):
    """Supported AI providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENCODE = "opencode"


@dataclass
class AIModel:
    """Represents an AI model."""

    name: str
    provider: ProviderType
    max_tokens: int = 4096


@dataclass
class AIResponse:
    """Standardized AI response."""

    content: str
    model: str
    usage: dict[str, int] | None = None
    raw_response: Any | None = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def complete(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        """Send a completion request to the AI."""

    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type."""

    def supports_structured_output(self) -> bool:
        """Whether provider supports structured JSON output."""
        return True
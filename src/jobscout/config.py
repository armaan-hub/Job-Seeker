"""Configuration management for Job Scout."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class ProviderConfig(BaseModel):
    """AI provider configuration."""

    api_key: str = Field(default="")
    base_url: str | None = Field(default=None)
    model: str | None = Field(default=None)
    enabled: bool = Field(default=True)


class JobScoutConfig(BaseModel):
    """Main configuration for Job Scout."""

    # Active provider selection
    active_provider: Literal["anthropic", "openai", "opencode"] = Field(
        default_factory=lambda: os.getenv("ACTIVE_PROVIDER", "anthropic")
    )

    # Provider-specific settings
    anthropic: ProviderConfig = Field(
        default_factory=lambda: ProviderConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        )
    )

    openai: ProviderConfig = Field(
        default_factory=lambda: ProviderConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
    )

    opencode: ProviderConfig = Field(
        default_factory=lambda: ProviderConfig(
            base_url=os.getenv("OPENCODE_BASE_URL", "http://localhost:4001"),
            api_key=os.getenv("OPENAI_API_KEY", "dummy"),
        )
    )

    # Job scraping settings
    job_sources: list[str] = Field(
        default_factory=lambda: ["linkedin", "indeed", "bayt", "naukrigulf"]
    )

    # Search defaults
    default_location: str = Field(default="Dubai, UAE")
    default_roles: list[str] = Field(
        default_factory=lambda: [
            "Financial Data Analyst",
            "Data Analyst",
            "Power BI Developer",
        ]
    )
    max_results: int = Field(default=20)

    # Profile paths
    profile_path: Path | None = Field(default=None)
    cv_path: Path | None = Field(default=None)

    # Output settings
    output_format: Literal["json", "text", "table"] = Field(default="table")
    detailed_output: bool = Field(default=False)

    @classmethod
    def from_env(cls) -> JobScoutConfig:
        """Load configuration from environment variables."""
        return cls()

    @classmethod
    def from_file(cls, path: Path) -> JobScoutConfig:
        """Load configuration from a YAML file."""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    def get_active_provider_config(self) -> ProviderConfig:
        """Get the active provider configuration."""
        return getattr(self, self.active_provider)


def get_config(config_path: Path | None = None) -> JobScoutConfig:
    """Get the application configuration."""
    if config_path and config_path.exists():
        return JobScoutConfig.from_file(config_path)
    return JobScoutConfig.from_env()

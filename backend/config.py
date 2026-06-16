"""
CodeLens EKOS Configuration Module.

Provides centralized application configuration using Pydantic Settings,
with support for .env file loading and environment variable overrides.
All settings are prefixed with CODELENS_ when read from the environment.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings for CodeLens EKOS.

    Settings are loaded in priority order:
    1. Environment variables (prefixed with CODELENS_)
    2. Values from .env file
    3. Default values defined here

    Attributes:
        app_name: Display name of the application.
        app_version: Current semantic version string.
        debug: Enable debug mode with verbose logging and auto-reload.
        db_path: Path to the SQLite database file.
        llm_provider: LLM backend to use. Phase 3 feature — "none" disables LLM.
        llm_model: Model identifier for the chosen LLM provider.
        llm_base_url: Base URL for self-hosted LLM providers (e.g. Ollama).
        openai_api_key: API key for OpenAI provider. Required only when llm_provider is "openai".
        max_file_size_mb: Maximum file size in MB that the ingestion pipeline will process.
        supported_languages: Programming languages supported for parsing and extraction.
        send_source_code_to_llm: Privacy guard — when False, raw source code is never sent to LLM.
    """

    # Application
    app_name: str = "CodeLens"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    db_path: str = "data/codelens.db"

    # LLM (Phase 3 — not used in Phase 1)
    llm_provider: str = "none"  # "none", "ollama", "openai"
    llm_model: str = "llama3.1"
    llm_base_url: str = "http://localhost:11434"
    openai_api_key: str | None = None

    # Ingestion
    max_file_size_mb: int = 10
    supported_languages: list[str] = ["python"]

    # Privacy
    send_source_code_to_llm: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CODELENS_")

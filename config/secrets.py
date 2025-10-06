"""
Secrets management for API keys and sensitive data.

Secrets are loaded from environment variables (.env file) and never stored in JSON.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Secrets(BaseSettings):
    """
    Secrets loaded from environment variables.

    These should NEVER be stored in JSON configuration files.
    Always use environment variables for sensitive data.
    """

    # LLM API Keys
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")

    # Tool API Keys
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    reddit_client_id: Optional[str] = Field(default=None, alias="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(default=None, alias="REDDIT_CLIENT_SECRET")

    # Database URLs (contain credentials)
    postgres_url: Optional[str] = Field(default=None, alias="POSTGRES_URL")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # LangSmith (observability)
    langsmith_api_key: Optional[str] = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="cortex-flow", alias="LANGSMITH_PROJECT")
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")

    # Active project selection
    active_project: str = Field(default="default", alias="ACTIVE_PROJECT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global secrets instance
_secrets: Optional[Secrets] = None


def get_secrets() -> Secrets:
    """
    Get secrets singleton instance.

    Loads secrets from .env file on first call.
    """
    global _secrets
    if _secrets is None:
        _secrets = Secrets()
    return _secrets


def reload_secrets() -> Secrets:
    """
    Reload secrets from environment.

    Useful for testing or after .env file changes.
    """
    global _secrets
    _secrets = Secrets()
    return _secrets


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a specific provider.

    Args:
        provider: Provider name (openai, anthropic, google, groq, openrouter)

    Returns:
        API key or None if not configured
    """
    secrets = get_secrets()
    provider_lower = provider.lower()

    if provider_lower == "openai":
        return secrets.openai_api_key
    elif provider_lower == "anthropic":
        return secrets.anthropic_api_key
    elif provider_lower == "google":
        return secrets.google_api_key
    elif provider_lower == "groq":
        return secrets.groq_api_key
    elif provider_lower == "openrouter":
        return secrets.openrouter_api_key
    elif provider_lower == "tavily":
        return secrets.tavily_api_key
    else:
        return None


def get_database_url(backend: str) -> Optional[str]:
    """
    Get database URL for a specific backend.

    Args:
        backend: Backend name (postgres, redis)

    Returns:
        Database URL or None if not configured
    """
    secrets = get_secrets()
    backend_lower = backend.lower()

    if backend_lower == "postgres" or backend_lower == "postgresql":
        return secrets.postgres_url
    elif backend_lower == "redis":
        return secrets.redis_url
    else:
        return None


def setup_langsmith():
    """
    Setup LangSmith tracing if configured.

    Sets environment variables for LangChain tracing.
    """
    secrets = get_secrets()

    if secrets.langsmith_api_key and secrets.langsmith_tracing:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = secrets.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = secrets.langsmith_project
        return True
    return False


def validate_secrets() -> dict:
    """
    Validate that required secrets are configured.

    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "missing": list[str],
            "warnings": list[str]
        }
    """
    secrets = get_secrets()
    missing = []
    warnings = []

    # Check for at least one LLM API key
    llm_keys = [
        secrets.openai_api_key,
        secrets.anthropic_api_key,
        secrets.google_api_key,
        secrets.groq_api_key,
        secrets.openrouter_api_key
    ]

    if not any(llm_keys):
        missing.append("At least one LLM API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)")

    # Check for database URLs if needed
    # (This will be checked at runtime based on project config)

    # Warnings for optional but recommended secrets
    if not secrets.tavily_api_key:
        warnings.append("TAVILY_API_KEY not set - web research will be limited")

    if not secrets.langsmith_api_key:
        warnings.append("LANGSMITH_API_KEY not set - tracing disabled")

    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "warnings": warnings
    }


def get_active_project() -> str:
    """Get name of active project from environment"""
    secrets = get_secrets()
    return secrets.active_project


def set_active_project(project_name: str):
    """
    Set active project in environment.

    Note: This only sets in current process, not in .env file.
    """
    os.environ["ACTIVE_PROJECT"] = project_name
    reload_secrets()

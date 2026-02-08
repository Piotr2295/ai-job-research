"""
Application configuration management.

Centralized configuration using Pydantic for validation and type safety.
"""

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "AI Job Research & Summary Agent"
    app_version: str = "2.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]

    # Rate Limiting
    rate_limit_per_hour: int = 100
    rate_limit_analyze: int = 20
    rate_limit_upload: int = 20
    rate_limit_search: int = 60
    rate_limit_rag: int = 30
    rate_limit_stream: int = 10

    # Database
    db_path: Path = Path(__file__).parent.parent / "mcp-server" / "job_research.db"
    db_timeout: float = 10.0

    # Storage
    cv_storage_path: Path = Path(__file__).parent.parent / "cv_storage"

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None
    json_logs: bool = False

    # API Keys (optional)
    github_token: str | None = None
    rapidapi_key: str | None = None
    openai_api_key: str | None = None
    pinecone_api_key: str | None = None

    # Agent Configuration
    max_tool_calls: int = 5
    max_reflection_iterations: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from environment
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")

        # Parse ALLOWED_ORIGINS
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        self.allowed_origins = [o.strip() for o in origins_str.split(",")]

        # Parse booleans
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.json_logs = os.getenv("JSON_LOGS", "false").lower() == "true"

        # Parse paths
        if os.getenv("DB_PATH"):
            self.db_path = Path(os.getenv("DB_PATH"))
        if os.getenv("CV_STORAGE_PATH"):
            self.cv_storage_path = Path(os.getenv("CV_STORAGE_PATH"))

        # Ensure directories exist
        self.cv_storage_path.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()

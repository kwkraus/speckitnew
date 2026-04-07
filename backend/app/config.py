from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PDF Multi-Agent RAG API"
    environment: str = "local"
    enable_auth: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    cosmos_endpoint: str = ""
    cosmos_key: str = ""
    cosmos_database: str = "pdf-rag"
    cosmos_documents_container: str = "documents"
    cosmos_conversations_container: str = "conversations"

    blob_connection_string: str = ""
    blob_container: str = "pdf-uploads"

    search_endpoint: str = ""
    search_api_key: str = ""
    search_index_name: str = "document-chunks"

    openai_endpoint: str = ""
    openai_api_key: str = ""
    openai_embedding_deployment: str = "text-embedding-3-large"
    openai_chat_deployment: str = "gpt-4o"

    doc_intelligence_endpoint: str = ""
    doc_intelligence_key: str = ""

    max_file_size_mb: int = 50
    max_concurrent_jobs: int = 10
    chunk_max_tokens: int = 1000
    chunk_overlap_tokens: int = 100

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


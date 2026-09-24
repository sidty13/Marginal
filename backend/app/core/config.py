"""
Central application configuration.

All values are loaded from environment variables (see .env.example).
Nothing here should be hard-coded per-deployment.
"""
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "Notebook RAG"
    ENV: str = "development"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.strip().startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/notebook_rag"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/notebook_rag"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v: str) -> str:
        if isinstance(v, str):
            import os
            import urllib.parse

            v = v.strip().strip("'").strip('"')
            if not v or "localhost" in v or "127.0.0.1" in v:
                for key in ("DATABASE_URL", "DATBASE_URL", "POSTGRES_URL", "NEON_DATABASE_URL", "DB_URL"):
                    val = os.environ.get(key)
                    if val and "localhost" not in val and "127.0.0.1" not in val:
                        v = val.strip().strip("'").strip('"')
                        break

            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

            parsed = urllib.parse.urlsplit(v)
            query_params = urllib.parse.parse_qsl(parsed.query)

            clean_params = []
            ssl_set = False
            for k, val in query_params:
                if k == "sslmode":
                    if val in ("require", "prefer", "verify-ca", "verify-full"):
                        clean_params.append(("ssl", "require"))
                        ssl_set = True
                    elif val == "disable":
                        clean_params.append(("ssl", "disable"))
                        ssl_set = True
                elif k == "ssl":
                    clean_params.append((k, val))
                    ssl_set = True
                elif k in ("timeout", "command_timeout", "statement_cache_size", "max_queries", "max_inactive_connection_lifetime"):
                    clean_params.append((k, val))
                # Discard channel_binding and other unsupported libpq query parameters

            if not ssl_set and (".neon.tech" in parsed.netloc or ".neon.tech" in v):
                clean_params.append(("ssl", "require"))

            new_query = urllib.parse.urlencode(clean_params)
            v = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))
        return v

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_sync_db_url(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().strip("'").strip('"')
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg2://", 1)
            elif v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # --- Storage ---
    UPLOAD_DIR: str = "./storage/uploads"

    # --- LLM / Embeddings ---
    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # --- Chunking ---
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 75

    # --- Retrieval ---
    TOP_K_VECTOR: int = 20
    TOP_K_BM25: int = 20
    TOP_K_FINAL: int = 6
    USE_RERANKER: bool = True

    # --- TTS (bonus: podcast) ---
    OPENAI_TTS_VOICE_HOST_A: str = "alloy"
    OPENAI_TTS_VOICE_HOST_B: str = "echo"

    # --- Auth (Clerk) ---
    # The Frontend API URL for your Clerk app, e.g. "https://your-app.clerk.accounts.dev"
    # (Clerk Dashboard -> Configure -> API Keys -> "Frontend API URL"), or your
    # production Clerk domain once you've set one up. Used to fetch Clerk's JWKS
    # and verify session tokens; leave unset and every request will be rejected.
    CLERK_ISSUER: str = ""

    # --- YouTube transcript proxy (optional) ---
    # If set, routes youtube_transcript_api requests through Webshare's
    # residential proxies instead of this server's own (often-blocked)
    # datacenter IP. Get credentials at webshare.io -> Dashboard -> Proxy.
    # Leave both blank to fall back to direct (unproxied) requests.
    WEBSHARE_PROXY_USERNAME: str = ""
    WEBSHARE_PROXY_PASSWORD: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

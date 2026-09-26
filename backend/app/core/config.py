from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    MISTRAL_API_KEY: str
    MISTRAL_MODEL: str

    LLM_PROVIDER: str
    MODEL_NAME: str

    LANGGRAPH_CHECKPOINT_DB: str = "data/langgraph_checkpoints.sqlite"

    EMBEDDING_MODEL: str
    QDRANT_URL: str
    QDRANT_COLLECTION: str
    EMBEDDING_DIMENSIONS: int
    OPENAI_BASE_URL: str
    OPENAI_API_KEY: str
    EMBEDDING_ENDPOINT: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]

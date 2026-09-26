from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    LLM_PROVIDER: str
    MODEL_NAME: str

    LANGGRAPH_CHECKPOINT_DB: str = "data/langgraph_checkpoints.sqlite"

    EMBEDDING_MODEL: str
    EMBEDDING_DIMENSIONS: int

    QDRANT_URL: str
    QDRANT_COLLECTION: str

    OPENAI_BASE_URL: str
    OPENAI_API_KEY: str
    EMBEDDING_ENDPOINT: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]

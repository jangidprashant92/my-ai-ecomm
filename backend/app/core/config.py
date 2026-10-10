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
    EVAL_JUDGE_MODEL: str

    RAG_RETRIEVAL_TYPE: str = "mmr"

    RAG_USE_MMR: bool = True
    RAG_MMR_FETCH_K: int = 12
    RAG_MMR_LAMBDA_MULT: float = 0.75

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]

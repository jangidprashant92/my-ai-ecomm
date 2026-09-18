from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    MISTRAL_API_KEY: str
    MISTRAL_MODEL: str

    LLM_PROVIDER: str
    MODEL_NAME: str

    LANGGRAPH_CHECKPOINT_DB: str = "data/langgraph_checkpoints.sqlite"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]

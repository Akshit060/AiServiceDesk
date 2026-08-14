from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-8b-8192"
    DATABASE_URL: str = "sqlite:///./servicedesk.db"

    # HuggingFace dataset paths
    HF_AGENTS_CSV: str = "hf://datasets/mindweave/help-desk-tickets/data/agents.csv"
    HF_CATEGORIES_CSV: str = "hf://datasets/mindweave/help-desk-tickets/data/categories.csv"
    HF_TICKETS_CSV: str = "hf://datasets/mindweave/help-desk-tickets/data/tickets.csv"
    HF_COMMENTS_CSV: str = "hf://datasets/mindweave/help-desk-tickets/data/comments.csv"

    # Minimum expected ticket count for seed-completion check
    SEED_EXPECTED_TICKETS: int = 1000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()

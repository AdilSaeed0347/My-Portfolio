"""
backend/config/settings.py
Single, clean Settings class — merges your original fields with the new email fields.
All secrets come from .env — NEVER hardcode API keys in this file.
"""

import os
import logging
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────
    API_V1_STR:   str = "/api/v1"
    PROJECT_NAME: str = "Portfolio RAG Chatbot"
    VERSION:      str = "1.0.0"
    APP_ENV:      str = "development"
    DEBUG:        bool = False

    # ── Server ─────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ───────────────────────────────────────────────────────────────
    # Local dev:  "*"
    # Production: "https://your-portfolio.vercel.app"
    # Set in Railway dashboard as an env var — do NOT hardcode production URLs here
    # During deployment, you will override this via environment variable.
# The value below is just a safe default — NOT used in production.
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ── Groq ───────────────────────────────────────────────────────────────
    # Never put real keys here — set them in .env or Railway env vars dashboard
    GROQ_API_KEY:     str = ""
    GROQ_MODEL_EN:    str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_MODEL_UR:    str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_MODEL_NAME:  str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_TEMPERATURE: float = 0.2
    GROQ_MAX_TOKENS:  int = 500

    # ── Resend (email) ──────────────────────────────────────────────────────
    # Never put real keys here — set them in .env or Railway env vars dashboard
    RESEND_API_KEY:         str = ""
    # LOCAL:      onboarding@resend.dev   (Resend sandbox, no domain needed)
    # PRODUCTION: portfolio@insightfolio.dev  (after DNS verified in Resend)
    RESEND_FROM_EMAIL:      str = "onboarding@resend.dev"
    CONTACT_RECEIVER_EMAIL: str = "adilsaeed047@gmail.com"

    # ── RAG / Vector store ─────────────────────────────────────────────────
    EMBEDDING_MODEL:      str = "sentence-transformers/all-MiniLM-L6-v2"
    RETRIEVAL_TOP_K:      int = 5
    MIN_SIMILARITY_SCORE: float = 0.3
    VECTOR_STORE_TYPE:    str = "faiss"
    VECTOR_STORE_PATH:    str = "./rag/vectorstore/"

    # ── Memory ─────────────────────────────────────────────────────────────
    MAX_CONVERSATION_TURNS: int = 5
    SESSION_CLEANUP_HOURS:  int = 24

    # ── Safety ─────────────────────────────────────────────────────────────
    MAX_QUERY_LENGTH:         int = 500
    ENABLE_CONTENT_FILTERING: bool = True

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE:  str = "logs/app.log"

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        case_sensitive    = True
        extra             = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Single global instance — import this everywhere
settings = get_settings()


def validate_settings() -> bool:
    """
    Validate critical settings at startup.
    Call this inside lifespan(), NOT at module level,
    so Railway env vars are loaded before validation runs.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing — set it in Railway env vars or .env")

    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — contact form emails will fail")

    # Use absolute paths — server starts from backend/ so relative paths
    # would create backend/rag/vectorstore instead of the correct root/rag/vectorstore
    project_root = Path(__file__).resolve().parent.parent.parent
    for directory in ["logs", "rag/vectorstore", "rag/embeddings"]:
        (project_root / directory).mkdir(parents=True, exist_ok=True)

    return True
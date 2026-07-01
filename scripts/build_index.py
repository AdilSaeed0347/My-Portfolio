#!/usr/bin/env python3
"""
scripts/build_index.py
Builds the RAG vector index from Adil.txt.
Cross-platform (Windows + Linux) — uses pathlib throughout.

Run from project root:
    python scripts/build_index.py
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent          # my-portfolio/
BACKEND_DIR  = PROJECT_ROOT / "backend"
RAG_DIR      = PROJECT_ROOT / "rag"
DOCS_DIR     = RAG_DIR / "documents"
VECTOR_DIR   = RAG_DIR / "vectorstore"
ADIL_FILE    = DOCS_DIR / "Adil.txt"

# Add backend to path so imports work
sys.path.insert(0, str(BACKEND_DIR))


# ── logging ──────────────────────────────────────────────────────────────────
def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "setup.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


# ── steps ────────────────────────────────────────────────────────────────────
def check_environment(logger: logging.Logger) -> bool:
    """Verify .env exists and GROQ_API_KEY is set."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        logger.error(".env file not found — create it with GROQ_API_KEY=...")
        return False

    from dotenv import load_dotenv
    load_dotenv(env_file)

    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY missing from .env")
        return False

    logger.info("Environment OK")
    return True


def ensure_directories(logger: logging.Logger) -> bool:
    """Create all required directories if they don't exist."""
    dirs = [
        DOCS_DIR,
        VECTOR_DIR,
        RAG_DIR / "embeddings",
        PROJECT_ROOT / "logs",
        BACKEND_DIR / "routes",
        BACKEND_DIR / "services",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ready: {d.relative_to(PROJECT_ROOT)}")
    return True


async def build_index(logger: logging.Logger) -> bool:
    """Initialise UltraPreciseRetriever — this builds and saves the index."""
    if not ADIL_FILE.exists():
        logger.error(f"Knowledge base not found: {ADIL_FILE}")
        return False

    try:
        from services.retriever import UltraPreciseRetriever

        logger.info("Building vector index …")
        retriever = UltraPreciseRetriever()
        await retriever.initialize()
        logger.info("Index built and saved to rag/vectorstore/")
        return True

    except Exception as exc:
        logger.error(f"Index build failed: {exc}", exc_info=True)
        return False


async def test_pipeline(logger: logging.Logger) -> bool:
    """Quick smoke-test — runs 2 queries through the full pipeline."""
    try:
        from services.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()
        await pipeline.initialize()

        queries = [
            "Who is Adil Saeed?",
            "What projects has Adil worked on?",
        ]

        for q in queries:
            result = await pipeline.process_query(q)
            answer  = result.get("answer", "")
            qt      = result.get("query_type", "")
            conf    = result.get("confidence", 0)
            logger.info(f"Query: '{q}'")
            logger.info(f"  type={qt}  confidence={conf:.2f}")
            logger.info(f"  answer={answer[:80]}...")

        logger.info("Smoke tests passed")
        return True

    except Exception as exc:
        logger.error(f"Smoke test failed: {exc}", exc_info=True)
        return False


# ── main ─────────────────────────────────────────────────────────────────────
async def main() -> bool:
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("RAG Index Builder")
    logger.info("=" * 50)

    steps = [
        ("Environment check",  lambda: check_environment(logger)),
        ("Directory setup",    lambda: ensure_directories(logger)),
        ("Build index",        lambda: asyncio.get_event_loop().run_until_complete(build_index(logger))
                                       if False else None),  # handled below
        ("Smoke test",         lambda: asyncio.get_event_loop().run_until_complete(test_pipeline(logger))
                                       if False else None),  # handled below
    ]

    # Run sync steps
    if not check_environment(logger):
        return False
    if not ensure_directories(logger):
        return False

    # Run async steps
    if not await build_index(logger):
        return False
    if not await test_pipeline(logger):
        return False

    logger.info("=" * 50)
    logger.info("Setup complete!")
    logger.info("Start the server with:")
    logger.info("  cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 --reload")
    logger.info("=" * 50)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
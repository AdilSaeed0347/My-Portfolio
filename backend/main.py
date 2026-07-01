"""
backend/main.py
FastAPI entry point — single app, single lifespan, all routers registered.
"""

import os
import sys
import time
import logging
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

if os.name == "nt":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings, validate_settings


def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    class UnicodeFormatter(logging.Formatter):
        def format(self, record):
            try:
                return super().format(record)
            except UnicodeEncodeError:
                record.msg = str(record.msg).encode("ascii", "replace").decode("ascii")
                return super().format(record)

    fmt = UnicodeFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        handlers=[file_handler, stream_handler],
    )


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Portfolio RAG Chatbot...")
    t0 = time.time()
    try:
        validate_settings()
        from services.rag_pipeline import RAGPipeline
        rag_pipeline = RAGPipeline()
        await rag_pipeline.initialize()
        app.state.rag_pipeline = rag_pipeline
        ms = (time.time() - t0) * 1000
        logger.info(f"READY in {ms:.0f}ms | Model: {settings.GROQ_MODEL_NAME}")
    except Exception as exc:
        logger.error(f"Startup failed: {exc}", exc_info=True)
        raise
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RAG-powered chatbot for Adil Saeed's portfolio",
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

_origins = (
    [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
    if settings.ALLOWED_ORIGINS != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    t = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.time() - t:.4f}"
    return response


from routes.chat    import router as chat_router
from routes.contact import router as contact_router

app.include_router(chat_router,    prefix=settings.API_V1_STR)
app.include_router(contact_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message":   "Portfolio RAG Chatbot API",
        "version":   settings.VERSION,
        "status":    "running",
        "groq_model": settings.GROQ_MODEL_NAME,
        "endpoints": {
            "chat":    f"{settings.API_V1_STR}/chat",
            "contact": f"{settings.API_V1_STR}/contact",
            "health":  "/health",
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status":            "healthy",
        "timestamp":         time.time(),
        "groq_configured":   bool(settings.GROQ_API_KEY),
        "resend_configured": bool(settings.RESEND_API_KEY),
        "env":               settings.APP_ENV,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": time.time(), "path": str(request.url.path)},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT,
                reload=settings.DEBUG, log_level=settings.LOG_LEVEL.lower())
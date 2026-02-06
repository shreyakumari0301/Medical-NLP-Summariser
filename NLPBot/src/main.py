"""NLP Conversation Intelligence — Channel Ingestion API entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.ingestion import router as ingest_router
from src.registry import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Conversation Intake API",
    description="Channel Ingestion → Conversation Registry → Transcription → Normalization → Stored",
    lifespan=lifespan,
)
app.include_router(ingest_router)


@app.get("/health")
def health():
    return {"status": "ok"}

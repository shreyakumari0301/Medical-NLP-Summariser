"""Channel Ingestion API: receive chat or voice, run intake pipeline, return conversation_id."""

from fastapi import APIRouter, HTTPException

from src.ingestion.payloads import (
    IncomingChatPayload,
    IncomingVoicePayload,
    IngestionResponse,
)
from src.ingestion.pipeline import process_chat, process_voice
from src.registry import get_conversation
from src.schemas import ConversationOutput

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/chat", response_model=IngestionResponse)
def ingest_chat(payload: IncomingChatPayload) -> IngestionResponse:
    """Incoming chat → Conversation Registry → Text Normalization → Raw + Clean stored."""
    cid = process_chat(payload)
    return IngestionResponse(
        conversation_id=cid,
        status="registered",
        message="Conversation ready for NLP",
    )


@router.post("/voice", response_model=IngestionResponse)
def ingest_voice(payload: IncomingVoicePayload) -> IngestionResponse:
    """Incoming call/voice → (Transcription Worker) → Text Normalization → Raw + Clean stored."""
    cid = process_voice(payload)
    return IngestionResponse(
        conversation_id=cid,
        status="registered",
        message="Conversation ready for NLP",
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationOutput)
def get_stored_conversation(conversation_id: str) -> ConversationOutput:
    """Retrieve stored conversation (raw + clean text, metadata) for NLP/analytics."""
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

"""Conversation Registry: persist conversation ID, speaker turns, timestamps, channel."""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from src.schemas import ChannelSource, ConversationOutput, SpeakerTurn
from src.schemas.contract import CompletenessStatus, ConversationMetadata

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "conversations.db"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                channel_source TEXT NOT NULL,
                raw_transcript TEXT NOT NULL,
                clean_text TEXT,
                speaker_turns_json TEXT NOT NULL,
                started_at TEXT,
                ended_at TEXT,
                language TEXT DEFAULT 'en',
                primary_intent TEXT,
                secondary_tags_json TEXT,
                extracted_fields_json TEXT,
                completeness_status TEXT DEFAULT 'unknown',
                auto_summary TEXT,
                lead_score REAL,
                geo_metadata_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def _turns_from_row(row: sqlite3.Row) -> list[SpeakerTurn]:
    raw = row["speaker_turns_json"]
    if not raw:
        return []
    data = json.loads(raw)
    return [SpeakerTurn(**t) for t in data]


def register_conversation(
    conversation_id: str,
    channel_source: ChannelSource,
    speaker_turns: list[SpeakerTurn],
    raw_transcript: str,
    clean_text: str | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
) -> None:
    turns_json = json.dumps(
        [t.model_dump(mode="json") for t in speaker_turns],
        default=str,
    )
    now = datetime.utcnow().isoformat() + "Z"
    with _conn() as c:
        c.execute(
            """
            INSERT OR REPLACE INTO conversations (
                conversation_id, channel_source, raw_transcript, clean_text,
                speaker_turns_json, started_at, ended_at, language,
                primary_intent, secondary_tags_json, extracted_fields_json,
                completeness_status, auto_summary, lead_score, geo_metadata_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'en', NULL, '[]', '{}', ?, NULL, NULL, '{}', ?, ?)
            """,
            (
                conversation_id,
                channel_source.value,
                raw_transcript,
                clean_text,
                turns_json,
                started_at,
                ended_at,
                CompletenessStatus.UNKNOWN.value,
                now,
                now,
            ),
        )


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def get_conversation(conversation_id: str) -> ConversationOutput | None:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()
    if not row:
        return None
    turns = _turns_from_row(row)
    meta = ConversationMetadata(
        conversation_id=row["conversation_id"],
        channel_source=ChannelSource(row["channel_source"]),
        started_at=_parse_iso(row["started_at"]),
        ended_at=_parse_iso(row["ended_at"]),
        language=row["language"] or "en",
        geo_metadata=json.loads(row["geo_metadata_json"] or "{}"),
    )
    return ConversationOutput(
        conversation_id=row["conversation_id"],
        raw_transcript=row["raw_transcript"],
        primary_intent=row["primary_intent"],
        secondary_tags=json.loads(row["secondary_tags_json"] or "[]"),
        extracted_structured_fields=json.loads(row["extracted_fields_json"] or "{}"),
        completeness_status=CompletenessStatus(row["completeness_status"] or "unknown"),
        auto_generated_summary=row["auto_summary"],
        lead_score=row["lead_score"],
        conversation_metadata=meta,
        clean_text=row["clean_text"],
        speaker_turns=turns,
    )


def generate_conversation_id() -> str:
    return f"conv_{uuid.uuid4().hex[:16]}"

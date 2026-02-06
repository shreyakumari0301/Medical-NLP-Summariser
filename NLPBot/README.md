# NLP Conversation Intelligence — Intake Pipeline

**Phase 0:** Text/recorded first, English, post-conversation, no fancy personalization.

**Phase 1:** One conversation → contract: `raw_transcript`, `primary_intent`, `secondary_tags`, `extracted_structured_fields`, `completeness_status`, `auto_generated_summary`, `lead_score`, `conversation_metadata` (+ `clean_text`, `speaker_turns`). See `src/schemas/contract.py`.

**Phase 2:** Intake flow:

```
Incoming Chat / Call → Channel Ingestion API → Conversation Registry
  → (Voice?) Transcription Worker → Text Normalization Worker
  → Raw + Clean Text Stored → Conversation Ready for NLP
```

## Run

```bash
cd c:\Users\shrey\NLPBot
pip install -r requirements.txt
uvicorn src.main:app --reload
```

- **POST /ingest/chat** — Send text chat (body: `{ "turns": [ { "speaker_id": "user", "text": "Hello" } ], "conversation_id": null }`).
- **POST /ingest/voice** — Send voice (body: `{ "transcript": "Pre-transcribed text" }` or `{ "audio_url": "https://..." }`).
- **GET /ingest/conversations/{conversation_id}** — Get stored conversation (raw + clean, metadata).
- **GET /health** — Health check.

Data is stored in `data/conversations.db` (SQLite).

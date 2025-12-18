from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Dict, List, Optional

import spacy
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

load_dotenv()

# Try to import alternative LLM providers
try:
    from langchain_community.chat_models import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class AnalyzeRequest(BaseModel):
    transcript: str
    patient_name: Optional[str] = None


try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    print(f"Warning: Failed to load spaCy model: {e}")
    nlp = None

# Initialize LLM based on environment variables
llm = None
use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
use_groq = os.getenv("USE_GROQ", "false").lower() == "true"

if use_ollama and OLLAMA_AVAILABLE:
    try:
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Optimize Mistral for CPU: smaller context, limited tokens, faster inference
        llm = ChatOllama(
            model=ollama_model, 
            base_url=ollama_base_url, 
            temperature=0.1,
            num_ctx=2048,  # Smaller context for faster processing (Mistral default is 8k)
            num_predict=256,  # Limit output to 256 tokens for faster responses
            top_k=20,  # Reduce sampling options for speed
            top_p=0.9,  # Nucleus sampling
        )
        print(f"✓ Using Ollama with model: {ollama_model} (CPU optimized)")
    except Exception as e:
        print(f"Warning: Failed to initialize Ollama: {e}")
elif use_groq and GROQ_AVAILABLE:
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        # Valid Groq models: llama-3.1-8b-instant, llama-3.1-70b-versatile, gemma-7b-it, llama-3.2-3b-instruct
        # Note: mixtral-8x7b-32768 has been decommissioned
        groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        if groq_api_key:
            # Use Groq via OpenAI-compatible interface
            llm = ChatOpenAI(
                model=groq_model,
                openai_api_key=groq_api_key,
                openai_api_base="https://api.groq.com/openai/v1",
                temperature=0.1,
            )
            print(f"✓ Using Groq with model: {groq_model}")
        else:
            print("Warning: GROQ_API_KEY not set")
    except Exception as e:
        print(f"Warning: Failed to initialize Groq: {e}")
else:
    # Default to OpenAI
    try:
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.1,
        )
        print("✓ Using OpenAI")
    except Exception as e:
        print(f"Warning: Failed to initialize OpenAI: {e}")
        llm = None

app = FastAPI(title="Medical NLP Pipeline", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_keywords(text: str, max_kw: int = 12) -> List[str]:
    """Extract medically relevant keywords, filtering out generic words"""
    if nlp is None:
        return []
    doc = nlp(text)
    
    # Strong medical/clinical terms to prioritize
    medical_terms = {
        "pain", "injury", "symptom", "diagnosis", "treatment", "therapy", "session",
        "accident", "whiplash", "physiotherapy", "painkiller", "medication", "discomfort",
        "stiffness", "tenderness", "movement", "recovery", "prognosis", "examination",
        "headache", "dizziness", "nausea", "photophobia", "neurological", "examination",
        "tension", "persistent", "chronic", "acute", "condition", "disorder", "syndrome"
    }
    
    # Filter out generic/weak words
    generic_words = {
        "that", "this", "the", "a", "an", "and", "or", "but", "if", "when", "where",
        "what", "which", "who", "how", "why", "afternoon", "morning", "evening", "night",
        "doctor", "patient", "physician", "bank", "thing", "way", "time", "day", "week",
        "month", "year", "today", "yesterday", "tomorrow", "daily", "your", "my", "their",
        "some", "any", "other", "more", "most", "very", "quite", "really", "just", "only"
    }
    
    # Weak medical phrases to exclude
    weak_phrases = {
        "your symptoms", "your condition", "your pain", "your treatment", "your recovery",
        "the accident", "the pain", "the treatment", "the condition", "the symptoms",
        "some discomfort", "some pain", "any pain", "any symptoms", "any treatment"
    }
    
    # Extract noun phrases (multi-word medical terms) - prioritize medical terminology
    phrases = set()
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip().lower()
        # Must be at least 4 chars, not generic, and contain medical terms or be a medical entity
        if (len(phrase) > 4 
            and not any(gw in phrase for gw in generic_words)
            and phrase not in weak_phrases
            and (any(term in phrase for term in medical_terms) 
                 or any(word in phrase for word in ["pain", "injury", "treatment", "therapy", "symptom", "diagnosis", "examination", "headache", "dizziness", "nausea"]))):
            phrases.add(phrase)
    
    # Extract medical entities (locations, dates, organizations) - only if medically relevant
    ents = {
        ent.text.strip()
        for ent in doc.ents
        if ent.label_ in {"ORG", "PERSON", "GPE", "NORP", "PRODUCT", "DATE", "TIME"}
        and len(ent.text.strip()) > 3
    }
    
    # Extract strong medical nouns only
    medical_nouns = set()
    for token in doc:
        lemma = token.lemma_.strip().lower()
        if (token.pos_ in {"NOUN", "PROPN"}
            and len(token.text) > 3
            and not token.is_stop
            and lemma not in generic_words
            and (lemma in medical_terms or any(term in lemma for term in medical_terms))):
            medical_nouns.add(lemma)
    
    # Combine and prioritize: medical phrases > medical nouns > entities
    combined = []
    # Add medical phrases first (highest priority)
    combined.extend(sorted(phrases))
    # Add medical nouns
    combined.extend(sorted(medical_nouns))
    # Add relevant entities last
    combined.extend(sorted(ents))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_combined = []
    for item in combined:
        item_lower = item.lower()
        if item_lower not in seen and item_lower not in generic_words:
            seen.add(item_lower)
            unique_combined.append(item)
    
    return unique_combined[:max_kw]


def classify_sentiment(text: str) -> Dict[str, str]:
    if llm is None:
        return {"Sentiment": "Neutral", "Confidence": 0.5, "error": "LLM not initialized"}
    try:
        prompt = ChatPromptTemplate.from_template(
            """Classify the patient's sentiment from this text as one of: Anxious, Neutral, or Reassured.
            
Text: {text}

Respond with only the sentiment label and a confidence score (0.0-1.0) as JSON: {{"sentiment": "...", "confidence": 0.0}}
"""
        )
        chain = prompt | llm
        result = chain.invoke({"text": text}).content
        try:
            import json
            parsed = json.loads(result)
            return {"Sentiment": parsed.get("sentiment", "Neutral"), "Confidence": float(parsed.get("confidence", 0.5))}
        except:
            # Fallback if JSON parsing fails
            sentiment = "Neutral"
            if any(word in result.lower() for word in ["anxious", "worried", "concerned", "nervous"]):
                sentiment = "Anxious"
            elif any(word in result.lower() for word in ["reassured", "relieved", "better", "good"]):
                sentiment = "Reassured"
            return {"Sentiment": sentiment, "Confidence": 0.7}
    except Exception as e:
        # Fallback on OpenAI errors (quota, API key, etc.)
        return {"Sentiment": "Neutral", "Confidence": 0.5, "error": f"OpenAI API error: {str(e)}"}


def classify_intent(text: str) -> Dict[str, str]:
    if llm is None:
        return {"Intent": "Reporting symptoms", "Confidence": 0.5, "error": "LLM not initialized"}
    try:
        # Improved prompt with better intent definitions
        prompt = ChatPromptTemplate.from_template(
            """Classify patient intent from this medical conversation. Choose ONE:
- "Seeking reassurance" - Patient asking if they'll be okay, expressing worry about recovery
- "Reporting symptoms" - Patient describing current or past symptoms
- "Reporting recovery status" - Patient updating on improvement/progress
- "Providing history" - Patient recounting past events, medical history
- "Expressing concern" - Patient showing worry or anxiety
- "Requesting treatment plan" - Patient actively asking what to do next for treatment

Text: {text}

Respond with JSON: {{"intent": "...", "confidence": 0.0}}"""
        )
        chain = prompt | llm
        result = chain.invoke({"text": text}).content
        try:
            import json
            parsed = json.loads(result)
            return {"Intent": parsed.get("intent", "Reporting symptoms"), "Confidence": float(parsed.get("confidence", 0.5))}
        except:
            # Fallback if JSON parsing fails
            intent = "Reporting symptoms"
            if "reassurance" in result.lower() or "worry" in result.lower():
                intent = "Seeking reassurance"
            elif "treatment" in result.lower() or "plan" in result.lower():
                intent = "Requesting treatment plan"
            elif "history" in result.lower() or "happened" in result.lower():
                intent = "Providing history"
            return {"Intent": intent, "Confidence": 0.7}
    except Exception as e:
        # Fallback on OpenAI errors (quota, API key, etc.)
        return {"Intent": "Reporting symptoms", "Confidence": 0.5, "error": f"OpenAI API error: {str(e)}"}


def build_summary_chain():
    if llm is None:
        return None
    prompt = ChatPromptTemplate.from_template(
        """Extract medical info as JSON from this transcript:
- Patient_Name: Full name (e.g., "Janet Jones" not "Ms. Jones")
- Symptoms: List of medical symptoms/phrases
- Diagnosis: Medical diagnosis
- Treatment: List of treatments/therapies
- Current_Status: Current patient condition
- Prognosis: Expected outcome

Use "Unknown" if missing. Return JSON only. Transcript: {transcript}"""
    )
    return prompt | llm


def build_soap_chain():
    if llm is None:
        return None
    # Clinical SOAP note prompt with better formatting
    prompt = ChatPromptTemplate.from_template(
        """Create a clinical SOAP note JSON from this medical transcript:

Subjective:
- Chief_Complaint: Clinical description (e.g., "Intermittent neck and back discomfort following motor vehicle accident")
- History_of_Present_Illness: Detailed timeline and progression

Objective:
- Physical_Exam: Clinical findings (range of motion, tenderness, etc.)
- Observations: Other relevant observations

Assessment:
- Diagnosis: Clinical diagnosis
- Severity: Mild/Moderate/Severe

Plan:
- Treatment: Only active treatments needed. If patient improving, state "No active treatment required; continue home exercises as advised" or similar
- Follow_Up: Follow-up recommendations

Use clinical language. Use "Unknown" if data absent. Return JSON only. Transcript: {transcript}"""
    )
    return prompt | llm


summary_chain = build_summary_chain()
soap_chain = build_soap_chain()


async def run_llm_chain(chain, input_data, default_error, timeout=120):
    """Run LLM chain asynchronously with timeout (longer for local Ollama on CPU)"""
    if chain is None:
        return default_error
    try:
        # Run in thread pool to avoid blocking, with longer timeout for CPU
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: chain.invoke(input_data).content
            ),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        return f'{{"error": "Request timeout after {timeout}s. Mistral on CPU is slow. Consider using Groq API or a smaller model."}}'
    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "abort" in error_msg.lower():
            return f'{{"error": "Connection closed - request took too long. Mistral on CPU needs 2-5 minutes. Please wait or use Groq API for faster results."}}'
        return f'{{"error": "LLM error: {error_msg}"}}'


async def run_sentiment_async(text: str, timeout=15) -> Dict[str, str]:
    """Async wrapper for sentiment classification with timeout"""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, classify_sentiment, text),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return {"Sentiment": "Neutral", "Confidence": 0.5, "error": "Timeout"}


async def run_intent_async(text: str, timeout=15) -> Dict[str, str]:
    """Async wrapper for intent classification with timeout"""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, classify_intent, text),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return {"Intent": "Reporting symptoms", "Confidence": 0.5, "error": "Timeout"}


@app.post("/analyze")
async def analyze(payload: AnalyzeRequest) -> Dict[str, object]:
    transcript = payload.transcript.strip()
    if not transcript:
        return {"error": "Transcript is required"}

    # Fast operations (spaCy) - run immediately
    keywords = extract_keywords(transcript)
    
    # Run all LLM calls in parallel with longer timeouts for local Ollama (CPU is slower)
    # Mistral on CPU can take 2-5 minutes, so we need very long timeouts
    sentiment_task = run_sentiment_async(transcript, timeout=30)
    intent_task = run_intent_async(transcript, timeout=30)
    summary_task = run_llm_chain(
        summary_chain, 
        {"transcript": transcript}, 
        '{"error": "LLM not initialized"}',
        timeout=120  # 2 minutes for Mistral on CPU
    )
    soap_task = run_llm_chain(
        soap_chain,
        {"transcript": transcript},
        '{"error": "LLM not initialized"}',
        timeout=120  # 2 minutes for Mistral on CPU
    )
    
    # Wait for all to complete in parallel, allow partial results
    results = await asyncio.gather(
        sentiment_task,
        intent_task,
        summary_task,
        soap_task,
        return_exceptions=True
    )
    
    # Handle results, converting exceptions to error dicts
    sentiment = results[0] if not isinstance(results[0], Exception) else {"Sentiment": "Neutral", "Confidence": 0.5, "error": str(results[0])}
    intent = results[1] if not isinstance(results[1], Exception) else {"Intent": "Reporting symptoms", "Confidence": 0.5, "error": str(results[1])}
    summary_json = results[2] if not isinstance(results[2], Exception) else f'{{"error": "{str(results[2])}"}}'
    soap_json = results[3] if not isinstance(results[3], Exception) else f'{{"error": "{str(results[3])}"}}'

    # Helper function to extract JSON from markdown code blocks
    def extract_json(text: str) -> dict:
        """Extract JSON from text, handling markdown code blocks"""
        if not text:
            return {}
        text = text.strip()
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        if text.startswith("```"):
            # Remove opening ```json or ```
            text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
            # Remove closing ```
            text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
            text = text.strip()
        # Try to parse as JSON directly
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object from text using regex
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            # If still fails, return raw text in error format
            return {"error": "Failed to parse JSON", "raw": text[:500]}  # Limit raw text length
    
    # Parse JSON results
    summary = extract_json(summary_json)
    soap = extract_json(soap_json)

    return {
        "patient_name": payload.patient_name or summary.get("Patient_Name", "Unknown"),
        "summary": summary,
        "keywords": keywords,
        "sentiment": sentiment,
        "intent": intent,
        "soap_note": soap,
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


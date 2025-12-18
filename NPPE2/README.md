# Physician Notetaker (LangChain, spaCy, FastAPI + Next.js)

End-to-end medical NLP pipeline: FastAPI backend for medical transcription, NLP-based summarization, sentiment analysis, and SOAP note generation. Features a dark-themed Next.js frontend ready for Vercel deployment.

## Features

- **Medical NLP Summarization**: Extracts symptoms, diagnosis, treatment, prognosis from transcripts
- **Sentiment & Intent Analysis**: Classifies patient sentiment (Anxious/Neutral/Reassured) and intent
- **SOAP Note Generation**: Automatically generates structured SOAP notes
- **Keyword Extraction**: Medically-relevant keyword extraction using spaCy
- **Multiple LLM Support**: OpenAI, Groq (free tier), or Ollama (local, free)
- **Parallel Processing**: Async execution for faster response times
- **Dark-themed UI**: Modern, responsive Next.js frontend

## Quickstart

### Backend (FastAPI)

1. **Setup environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. **Configure LLM provider** (choose one):

   **Option A: Groq (Recommended - Free, Fast)**
   ```bash
   # Sign up at https://console.groq.com/
   # Get API key, then create .env file:
   USE_GROQ=true
   GROQ_API_KEY=your-groq-api-key
   GROQ_MODEL=llama-3.1-8b-instant
   ```

   **Option B: Ollama (Free, Local)**
   ```bash
   # Install Ollama: https://ollama.com/download
   ollama pull mistral  # or llama3.2, phi3:mini
   # Then create .env file:
   USE_OLLAMA=true
   OLLAMA_MODEL=mistral
   OLLAMA_BASE_URL=http://localhost:11434
   ```

   **Option C: OpenAI (Paid)**
   ```bash
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_MODEL=gpt-3.5-turbo
   ```

3. **Run server:**
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend (Next.js, Vercel-ready)

1. **Setup:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure backend URL** (create `.env.local`):
   ```
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   # Or your deployed backend URL for production
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Deploy to Vercel:**
   - Push `frontend/` folder to GitHub
   - Import to Vercel
   - Set `NEXT_PUBLIC_BACKEND_URL` environment variable
   - Deploy

## API Endpoints

### `POST /analyze`
Analyze a medical transcript and extract structured information.

**Request:**
```json
{
  "transcript": "Physician: How are you feeling? Patient: I have neck pain...",
  "patient_name": "Janet Jones"  // Optional
}
```

**Response:**
```json
{
  "patient_name": "Janet Jones",
  "summary": {
    "Patient_Name": "Janet Jones",
    "Symptoms": ["neck pain", "back pain"],
    "Diagnosis": "Whiplash injury",
    "Treatment": ["Physiotherapy", "Painkillers"],
    "Current_Status": "Improving",
    "Prognosis": "Full recovery expected"
  },
  "keywords": ["whiplash injury", "neck pain", "physiotherapy", "painkillers"],
  "sentiment": {
    "Sentiment": "Reassured",
    "Confidence": 0.80
  },
  "intent": {
    "Intent": "Reporting recovery status",
    "Confidence": 0.75
  },
  "soap_note": {
    "Subjective": {...},
    "Objective": {...},
    "Assessment": {...},
    "Plan": {...}
  }
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{"status": "ok"}
```

## Pipeline Details

### Medical NLP Summarization
- **NER/Keywords**: spaCy `en_core_web_sm` with medical term filtering
- **Summarization**: LangChain prompts extract structured JSON (Patient_Name, Symptoms, Diagnosis, Treatment, Current_Status, Prognosis)
- **SOAP Notes**: Automated generation with clinical formatting
- **Missing Data Handling**: Returns `"Unknown"` or `[]` for ambiguous/missing fields

### Sentiment & Intent Analysis
- **Sentiment Classification**: Anxious, Neutral, or Reassured
- **Intent Detection**: Seeking reassurance, Reporting symptoms, Reporting recovery status, Expressing concern, Requesting treatment plan, Providing history
- **Implementation**: LLM-based classification with fallback handling

### Performance Optimizations
- **Parallel Processing**: All LLM calls run concurrently using `asyncio.gather()`
- **Timeout Handling**: Configurable timeouts prevent hanging requests
- **Error Recovery**: Graceful fallbacks for failed operations
- **JSON Parsing**: Handles markdown code blocks and malformed JSON

## LLM Provider Options

### Groq (Recommended)
- **Free tier available**
- **Fast GPU inference** (5-10 seconds)
- **Models**: `llama-3.1-8b-instant`, `llama-3.1-70b-versatile`, `gemma-7b-it`
- **Setup**: Sign up at https://console.groq.com/

### Ollama (Local)
- **Completely free**
- **Runs locally** (no API costs)
- **Slower on CPU** (2-5 minutes for 7B models)
- **Models**: `mistral`, `llama3.2`, `phi3:mini` (faster)
- **Setup**: Install from https://ollama.com/

### OpenAI
- **Paid API** (requires credits)
- **High quality** results
- **Models**: `gpt-3.5-turbo`, `gpt-4o`

## Project Structure

```
NPPE2/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables (create this)
├── frontend/
│   ├── app/
│   │   ├── page.tsx       # Main UI component
│   │   ├── layout.tsx     # App layout
│   │   └── globals.css    # Dark theme styles
│   ├── package.json
│   └── next.config.mjs
├── env.example            # Environment variable template
├── FREE_SETUP.md          # Free LLM setup guide
└── README.md
```

## Technical Details

### Ambiguous/Missing Data Handling
- Prompts explicitly request `"Unknown"` for missing fields
- Rule-based fallbacks for sentiment/intent classification
- JSON parsing with error recovery

### Pre-trained Models
- **Summarization/SOAP**: LangChain with OpenAI/Groq/Ollama
- **Keywords**: spaCy `en_core_web_sm` with medical term filtering
- **Sentiment/Intent**: LLM-based classification

### Fine-tuning Recommendations
- **Medical Sentiment**: Fine-tune on `emilyalsentzer/Bio_ClinicalBERT` with `Anxious/Neutral/Reassured` labels
- **Datasets**: MEDIQA-AnS, MTSamples, i2b2/MADE for clinical language
- **SOAP Mapping**: Supervised learning on paired transcript→SOAP datasets with validation rules

## Troubleshooting

### Backend Issues
- **Module not found**: Ensure venv is activated and dependencies installed
- **spaCy model missing**: Run `python -m spacy download en_core_web_sm`
- **Ollama slow**: Use smaller models (`phi3:mini`) or switch to Groq API
- **Connection refused**: Ensure backend runs with `--host 0.0.0.0` for WSL

### Frontend Issues
- **Cannot connect to backend**: Check `NEXT_PUBLIC_BACKEND_URL` matches backend URL
- **CORS errors**: Backend CORS is configured for all origins

## License

MIT


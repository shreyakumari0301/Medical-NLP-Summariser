# Free LLM Setup Guide

## Option 1: Ollama (Recommended - Completely Free, Runs Locally)

### Installation:
1. **Install Ollama:**
   - Windows: Download from https://ollama.com/download
   - WSL: `curl -fsSL https://ollama.com/install.sh | sh`

2. **Pull a model:**
   ```bash
   ollama pull llama3.2  # or mistral, gemma, etc.
   ```

3. **Update your `.env` file:**
   ```
   USE_OLLAMA=true
   OLLAMA_MODEL=llama3.2
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. **Install langchain-community:**
   ```bash
   pip install langchain-community
   ```

### Option 2: Groq API (Free Tier - Fast, Cloud-based)

1. **Sign up:** https://console.groq.com/ (free tier available)

2. **Get API key** from Groq dashboard

3. **Update your `.env` file:**
   ```
   USE_GROQ=true
   GROQ_API_KEY=your-groq-api-key
   GROQ_MODEL=llama-3.1-8b-instant
   ```

4. **Install groq package:**
   ```bash
   pip install langchain-groq
   ```

### Option 3: Together.ai (Free Credits)

1. **Sign up:** https://together.ai/ (free credits)

2. **Get API key**

3. **Update your `.env` file:**
   ```
   USE_TOGETHER=true
   TOGETHER_API_KEY=your-together-api-key
   TOGETHER_MODEL=meta-llama/Llama-3-8b-chat-hf
   ```

4. **Install:**
   ```bash
   pip install langchain-together
   ```


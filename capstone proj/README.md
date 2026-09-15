# QM Assistant

A conversational AI assistant and voice-enabled chat widget built for QM Logics. Integrates FastAPI, Groq LLM inference, Deepgram voice synthesis, and dynamic lead qualification actions.

---

## Overview

QM Assistant serves as an automated representative on the QM Logics website. It answers client inquiries strictly using an internal knowledge base, routes users to relevant service pages, adheres to strict pricing guardrails, and provides speech-to-text and text-to-speech interaction.

---

## Tech Stack

- **Backend**: FastAPI, Uvicorn
- **LLM Inference**: Groq API (`openai/gpt-oss-120b`)
- **Text-to-Speech (TTS)**: Deepgram Aura (`aura-2-athena-en`)
- **Speech-to-Text (STT)**: Web Speech API (browser native)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3

---

## Project Structure

```text
├── bot.HTML              # Frontend chat widget with audio and STT support
├── main.py               # FastAPI backend (chat, voice, session management)
├── config.json           # Agent persona, service URLs, and response rules
├── qm_knowledge.txt      # Ground truth knowledge base
├── requirements.txt      # Python dependencies
├── test_deepgram.py      # Deepgram TTS test script
├── test_voice.py         # ElevenLabs fallback test script
├── logo.png              # Header branding asset
└── .env                  # Environment variables and API keys
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+
- Groq API Key
- Deepgram API Key

### 2. Environment Setup

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key  # Optional fallback
```

### 3. Installation

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Running the Application

Start the backend server:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open `bot.HTML` in any modern browser to use the chat widget.

---

## API Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health check |
| `GET` | `/starter-questions` | Retrieves starter prompt chips |
| `POST` | `/chat` | Processes user messages, returns response and CTA actions |
| `POST` | `/speak` | Streams MP3 audio generated from input text |

---

## Core System Guardrails

- **Strict Grounding**: Answers are restricted to facts explicitly stated in `qm_knowledge.txt`.
- **Zero-Number Pricing Policy**: Never quotes rates, fees, or project estimates. Defers pricing inquiries to custom quotes via `info@qmlogics.com`.
- **Dynamic Action Injection**: Automatically returns contextual action buttons (service links, consultation bookings) based on intent detection flags (`###NUDGE_YES###` / `###NUDGE_NO###`).
- **Session Handling**: In-memory session tracking with a 20-message sliding window and FIFO eviction at 500 sessions.

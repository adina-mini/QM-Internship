import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def load_agent_config(config_path="config.json"):
    with open(config_path, "r") as f:
        config = json.load(f)
    with open(config["kb_file"], "r") as f:
        config["knowledge"] = f.read()
    return config


CONFIG = load_agent_config()


def build_system_prompt(config: dict) -> str:
    return f"""You are {config['agent_name']}, an assistant for this company.

TONE: {config['tone']}

RULES:
1. Answer ONLY using the information in the KNOWLEDGE BASE below. Do not use outside knowledge.
2. If the answer is not in the knowledge base, respond EXACTLY with: "{config['fallback_message']}"
3. If the user asks about pricing, cost, rates, or budget, respond EXACTLY with: "{config['pricing_redirect']}"
4. Never invent facts, numbers, dates, or claims not present in the knowledge base.
5. Keep answers concise and conversational — 2-4 sentences unless the question needs a list.

KNOWLEDGE BASE:
{config['knowledge']}
"""


sessions: dict[str, list] = {}
# MAX_SESSIONS = 500


def make_session_key(client_id: str, session_id: str) -> str:
    return f"{client_id}:{session_id}"

    # def evict_oldest_if_needed():
    if len(sessions) > MAX_SESSIONS:
        oldest_key = next(
            iter(sessions)
        )  # dict preserves insertion order in Python 3.7+
        del sessions[oldest_key]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


@app.get("/starter-questions")
def get_starter_questions():
    return {"questions": CONFIG.get("starter_questions", [])}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_key = make_session_key(CONFIG["client_id"], req.session_id)
    history = sessions.get(session_key, [])
    history.append({"role": "user", "content": req.message})

    messages = [{"role": "system", "content": build_system_prompt(CONFIG)}] + history

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.3,
        max_tokens=400,
    )

    reply = completion.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    sessions[session_key] = history[-10:]  # avoid unbounded growth
    # evict_oldest_if_needed()

    return ChatResponse(reply=reply)


@app.get("/health")
def health():
    return {"status": "ok", "client": CONFIG["client_id"]}

import json
import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

load_dotenv()

# FASTAPI SETUP
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# LOADING CONFIG FILE
def load_agent_config(config_path="config.json"):
    with open(config_path, "r") as f:
        config = json.load(f)
    with open(config["kb_file"], "r") as f:
        config["knowledge"] = f.read()
    return config


CONFIG = load_agent_config()


# SYSTEM PROMPT
def build_system_prompt(config: dict) -> str:
    return f"""You are {config['agent_name']}, speaking on behalf of QM Logics as part of the team — not a third-party bot describing the company from outside.

TONE: {config['tone']}

RULES:
1. Answer ONLY using the information in the KNOWLEDGE BASE below. Do not use outside knowledge.
2. When a user asks if you offer a specific service, reason about whether it reasonably falls under one of the listed service categories, even if the exact wording isn't identical. Do not require an exact keyword match.
3. If the question is plausibly related to QM Logics' business (IT services, software, tech consulting, potential project work) but the specific answer isn't in the knowledge base, respond EXACTLY with: "{config['fallback_message']}"
4. If the question has NOTHING to do with QM Logics or its business at all (e.g. general knowledge, entertainment, politics, unrelated topics), respond EXACTLY with: "{config['off_topic_message']}"
5. If the user asks about pricing, cost, rates, budget, or how much something costs — including mentioning a tight or limited budget — respond warmly and reassuringly, like a helpful human would. Acknowledge what they specifically said (e.g. if they mention a tight budget, reassure them the team can work with their situation and find what fits). Always end by explaining that the final cost depends on project scope, and direct them to email info@qmlogics.com or use the Request a Quote form for a custom quote. HARD CONSTRAINT, no exceptions: never state any number, dollar amount, hourly rate, or percentage — not even one from the knowledge base — under any circumstances. This overrides rule 1. If you're unsure whether something counts as a number, leave it out.
6. Never invent facts, numbers, dates, or claims not present in the knowledge base.
7. Keep answers concise and conversational — 2-4 sentences unless the question needs a list.
8. When you mention a specific service by its exact name (e.g. "Web Development", "Generative AI"), or a specific page like "Refund Policy", "Blog", or "Careers", use that exact name so it can be linked automatically. Don't paraphrase these names.
9. Always write the company name exactly as "QM Logics" — both words capitalized, never lowercase or all-caps.
10. Speak as part of QM Logics, in first person plural — say "we offer," "our team," "we've built," never "they offer" or "QM Logics offers" as if describing an outside company.
11. You may use **bold** for emphasis and "- " for bullet points when listing multiple items — this will be rendered properly, so format naturally where it helps readability.
12. Whenever you mention the CEO's name, always wrap it in bold, like **Mudassir Saeed** — never write it as plain text.
13. Do NOT include markdown links like [text](url) or raw URLs in your responses — relevant links are added automatically as clickable buttons below your message. Just mention the service or page by name in plain text; never write out a URL yourself.
14. If someone asks why they should choose QM Logics over another company, or how you compare to competitors, give a genuine, specific, confident answer using what's actually in the knowledge base (experience, approach, testimonials, quality process) — don't be generic or evasive.
15. After you finish your reply, add this exact token on its own at the very end: ###NUDGE_YES### if the user's message asks about pricing, cost, budget, or rates, OR asks about booking a consultation, scheduling a meeting or call, talking to the team, comparing QM Logics to competitors, asking why they should choose QM Logics, or expressing genuine intent to start a project — otherwise add ###NUDGE_NO### instead. This token is a hidden signal that gets removed before the user sees your reply — always include exactly one of these two tokens, with no extra formatting around it.
16. QM Logics has real pages for Careers, Blog, and Refund Policy. If someone asks about these but the specific details (e.g. exact job openings, specific blog post titles) aren't in the knowledge base, do NOT use the fallback message. Instead, acknowledge the page exists, mention you don't have the specific live details on hand, and point them to check the page directly by name (e.g. "You can check our Careers page for current openings.").
KNOWLEDGE BASE:
{config['knowledge']}
"""


def parse_reply_and_nudge(raw_reply: str) -> tuple[str, bool]:
    has_yes = bool(re.search(r"###NUDGE_YES###", raw_reply))
    has_no = bool(re.search(r"###NUDGE_NO###", raw_reply))
    clean_reply = re.sub(r"###NUDGE_(YES|NO)###", "", raw_reply).strip()
    should_nudge = has_yes and not has_no
    return clean_reply, should_nudge


sessions: dict[str, list] = {}
MAX_SESSIONS = 500
MESSAGE_COUNT_THRESHOLD = 4


def make_session_key(client_id: str, session_id: str) -> str:
    return f"{client_id}:{session_id}"


def evict_oldest_if_needed():
    if len(sessions) > MAX_SESSIONS:
        oldest_key = next(iter(sessions))
        del sessions[oldest_key]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class Action(BaseModel):
    label: str
    url: str


class ChatResponse(BaseModel):
    reply: str
    actions: list[Action] = []


def find_service_actions(reply_text: str, config: dict) -> list[Action]:
    matched = []
    for service in config.get("services", []):
        if service["name"].lower() in reply_text.lower():
            matched.append(
                Action(label=f"Explore {service['name']}", url=service["url"])
            )
    return matched


def find_page_actions(reply_text: str, config: dict) -> list[Action]:
    matched = []
    for page in config.get("pages", []):
        if page["name"].lower() in reply_text.lower():
            matched.append(Action(label=f"View {page['name']}", url=page["url"]))
    return matched


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

    raw_reply = completion.choices[0].message.content
    if not raw_reply:
        raw_reply = "Sorry, I didn't quite catch that — could you rephrase your question? ###NUDGE_NO###"

    reply, model_flagged_nudge = parse_reply_and_nudge(raw_reply)

    history.append({"role": "assistant", "content": reply})
    sessions[session_key] = history[-20:]
    evict_oldest_if_needed()

    actions = find_service_actions(reply, CONFIG)
    actions += find_page_actions(reply, CONFIG)

    has_single_service = len(actions) == 1
    user_message_count = sum(1 for m in history if m["role"] == "user")
    hit_count_threshold = user_message_count >= MESSAGE_COUNT_THRESHOLD

    should_show_consult_button = (
        model_flagged_nudge or has_single_service or hit_count_threshold
    )

    # CONSULTATION BUTTON SHOW BASED ON NUDGE FLAG
    if should_show_consult_button:
        consultation_url = CONFIG.get("consultation_url", "")
        if consultation_url:
            actions.append(Action(label="Book a Consultation", url=consultation_url))

    return ChatResponse(reply=reply, actions=actions)


@app.get("/health")
def health():
    return {"status": "ok", "client": CONFIG["client_id"]}

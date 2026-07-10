import os
import asyncio
import json
import httpx
from dotenv import load_dotenv
from groq import AsyncGroq, RateLimitError
import inspect
import re

load_dotenv()

# API RETRIEVAL
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")
client = AsyncGroq(api_key=api_key)

# FILE BASED PERSISTENT MEMORY
MEMORY_FILE = "chat_history.json"
SUMMARY_FILE = "summary.json"
ENTITIES_FILE = "entities.json"


# LOAD AND SAVE FUNCTIONS
def load_history():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(history):
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def load_summary():
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE, "r") as f:
            return json.load(f).get("summary", "")
    else:
        # Create the file if it doesn't exist
        with open(SUMMARY_FILE, "w") as f:
            json.dump({"summary": ""}, f, indent=2)
        return ""


def save_summary():
    with open(SUMMARY_FILE, "w") as f:
        json.dump({"summary": conversation_summary}, f, indent=2)


def load_entities():
    if os.path.exists(ENTITIES_FILE):
        with open(ENTITIES_FILE, "r") as f:
            return json.load(f)
    return {}


def save_entities(entities):
    with open(ENTITIES_FILE, "w") as f:
        json.dump(entities, f, indent=2)


# MEMORY TRIMMING
max_history = 6


# SUMMARIZATION + TRIMMING (Hybrid Memory)

conversation_summary = load_summary()


async def summarize_old_messages(history):
    global conversation_summary
    if not history:
        return

    # Format ALL messages in history for LLM
    convo_text = "\n".join(
        [f"{msg['role'].upper()}: {msg['content']}" for msg in history]
    )

    # Create a summary from ALL messages in history
    summary_prompt = f"""Summarize this entire conversation in 2-3 sentences under 500 characters.
Keep important facts, names, locations, decisions, and preferences.

Full Conversation:
{convo_text}

Return only the summary, no extra text."""

    result = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": summary_prompt}],
        timeout=15.0,
    )

    conversation_summary = result.choices[0].message.content.strip()
    save_summary()


async def manage_memory(history):
    if len(history) > max_history:
        # Keep only max_history number of recent messages
        old_messages = history[:-max_history]  # Messages to remove
        recent_messages = history[-max_history:]  # Messages to keep

        # Summarize ALL messages (old + recent) - this will have the FULL conversation
        await summarize_old_messages(history)  # Pass ALL history, not just old_messages

        return recent_messages
    return history


# ENTITY MEMORY (LLM Based)

entity_memory = load_entities()


async def extract_entities(prompt: str, response: str):
    global entity_memory

    extraction_prompt = f"""Extract only stable long-term facts from this conversation that are worth remembering permanently.

User said: {prompt}
Assistant said: {response}

Return ONLY a JSON object with relevant keys. Examples of what to extract:
Personal: name, location, age, profession, university, major
Purchases: item bought, price, brand, store, date
Preferences: likes, dislikes, favorite things
Goals: what user wants to do or achieve
Ignore: greetings, weather queries, calculations, currency conversions, and one-time requests.

Return a valid JSON object only. No markdown, no code fences, no explanation.
If nothing worth remembering, return {{}}

Example output: {{"name": "Adina", "location": "Bahawalpur", "major": "AI"}}"""

    result = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": extraction_prompt}],
        timeout=10.0,
    )

    try:
        text = result.choices[0].message.content.strip()
        extracted = json.loads(text)
        if isinstance(extracted, dict):
            # only store non-empty key-value pairs
            valid = {k: v for k, v in extracted.items() if k and v}
            entity_memory.update(valid)
            save_entities(entity_memory)
    except Exception as e:
        print(f"Entity extraction failed: {e}")


# MEMORY STATUS PRINT
def print_memory_status():
    print("\n--- MEMORY STATUS ---")
    print(f"History: {len(conversation_history)} messages")
    print(f"Summary: {conversation_summary or 'empty'}")
    print(f"Entities: {entity_memory or 'none'}")
    print("---------------------\n")


conversation_history = load_history()


# FUNCTION IMPLEMENTATION OF TOOLS
async def get_weather(city: str) -> str:
    async with httpx.AsyncClient() as http:
        r = await http.get(f"https://wttr.in/{city}?format=3", timeout=10.0)
        return r.text


def calculate(expression: str) -> str:
    if not re.fullmatch(r"[0-9+\-*/().%\s]+", expression):
        return "Invalid mathematical expression."
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Math failed: {e}"


async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    async with httpx.AsyncClient() as http:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        r = await http.get(url, timeout=10.0)
        data = r.json()
        rate = data["rates"][to_currency.upper()]
        converted = amount * rate
        return (
            f"{amount} {from_currency.upper()} = {converted:.2f} {to_currency.upper()}"
        )


# TOOL DEFINITION
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "ONLY use this tool when user explicitly asks about weather, temperature, or climate. Do NOT use for city names, locations, greetings, or general conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "city name e.g london, bwp, tokyo",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "convert currency from one to other",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount to convert"},
                    "from_currency": {
                        "type": "string",
                        "description": "current to be converted from e.g USD, EUR, PKR",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "currency to converted to e.g INR, EUR",
                    },
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "ONLY evaluate arithmetic expressions such as addition, subtraction, multiplication, division, parentheses and percentages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "e.g 42 * 3 + 10"}
                },
                "required": ["expression"],
            },
        },
    },
]

TOOL_MAP = {
    "get_weather": get_weather,
    "calculate": calculate,
    "convert_currency": convert_currency,
}

# SYSTEM PROMPT
system_prompt = """You are a helpful assistant.

CRITICAL RULES FOR TOOL USE:

1. WEATHER TOOL (get_weather):
   - ONLY call when user asks about weather, temperature, or climate conditions.
   - NEVER call when user mentions a city in any other context (e.g., "I'm from BWP", "I live in Lahore").

2. CALCULATE TOOL (calculate):
   - ONLY call when user asks for math calculations.
   - NEVER call for counting messages or general number questions.

3. CURRENCY TOOL (convert_currency):
   - ONLY call when user asks about currency conversion.

4. FOR ALL OTHER QUESTIONS:
   - Respond directly from your knowledge or conversation history.
   - This includes: greetings, name, university, location, message count, and general chat.

You have access to conversation summary and persistent user memory to answer questions about past chats."""


# ASK_GROQ FUNCTION
async def ask_groq(prompt: str, retries: int = 3) -> str:
    global conversation_history, conversation_summary, entity_memory

    if not isinstance(conversation_history, list):
        conversation_history = []

    for attempt in range(retries):
        try:
            # BUILD MESSAGES
            messages = [{"role": "system", "content": system_prompt}]

            if conversation_summary:
                messages.append(
                    {
                        "role": "system",
                        "content": f"Conversation Summary: {conversation_summary}",
                    }
                )

            if entity_memory:
                entity_text = " | ".join(
                    [f"{k}: {v}" for k, v in entity_memory.items()]
                )
                messages.append(
                    {
                        "role": "system",
                        "content": f"Persistent User Memory: {entity_text}",
                    }
                )

            messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools,
                timeout=30.0,
            )

            tool_calls = response.choices[0].message.tool_calls

            if tool_calls:
                tool_call = tool_calls[0]
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                fn = TOOL_MAP.get(name)
                if not fn:
                    return f"unknown tool: {name}"
                print(f" TOOL CALLED: {name} with args: {args}")
                result = (
                    await fn(**args) if inspect.iscoroutinefunction(fn) else fn(**args)
                )
                print(f"TOOL RESULT: {result}")

                # TOOL CALL FORMATTING - serialization fix
                messages.append(
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                        ],
                    }
                )
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                )

                # SEND TOOL RESULT BACK TO LLM FOR FORMATTING
                final = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    timeout=30.0,
                )
                final_response = final.choices[0].message.content

                # EXTRACT ENTITIES + SAVE HISTORY
                await extract_entities(prompt, final_response)
                conversation_history.append({"role": "user", "content": prompt})
                conversation_history.append(
                    {"role": "assistant", "content": final_response}
                )
                conversation_history = await manage_memory(conversation_history)
                save_history(conversation_history)
                return final_response

            direct_response = response.choices[0].message.content

            # EXTRACT ENTITIES + SAVE HISTORY
            await extract_entities(prompt, direct_response)
            conversation_history.append({"role": "user", "content": prompt})
            conversation_history.append(
                {"role": "assistant", "content": direct_response}
            )
            conversation_history = await manage_memory(conversation_history)
            save_history(conversation_history)
            return direct_response

        # ERROR HANDLING
        except RateLimitError:
            print(f"[{attempt+1}/{retries}] rate limited, waiting 10s")
            await asyncio.sleep(10)
        except Exception as e:
            wait = 2**attempt
            print(f"[{attempt+1}/{retries}] error: {e}, retrying in {wait}s")
            await asyncio.sleep(wait)

    raise RuntimeError(f"all {retries} attempts failed")


# MAIN
async def main():
    print(" Groq Tool Calling Agent")
    print("Type 'exit' to quit. Type 'memory' to see memory status.\n")

    while True:
        prompt = input("You: ")

        if prompt.lower() == "exit":
            print("Goodbye!")
            break

        if prompt.lower() == "memory":
            print_memory_status()
            continue

        try:
            result = await ask_groq(prompt)
            print(f"\nGroq: {result}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
from dotenv import load_dotenv
from groq import AsyncGroq, RateLimitError

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found. Check your .env file.")

client = AsyncGroq(api_key=api_key)

# Accepts the entire history list instead of a single string prompt
async def ask_groq(messages: list, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                # Pass the complete conversation context window
                messages=messages,
                timeout=30.0
            )
            # FIXED: Added  to target the first choice object in the list
            return response.choices.message.content

        except RateLimitError:
            wait = 10
            print(f"[{attempt+1}/{retries}] Rate limited — waiting {wait}s...")
            await asyncio.sleep(wait)

        except Exception as e:
            wait = 2 ** attempt
            if "timeout" in str(e).lower():
                print(f"[{attempt+1}/{retries}] Timeout — retrying in {wait}s...")
            else:
                print(f"[{attempt+1}/{retries}] Error: {e} — retrying in {wait}s...")
            await asyncio.sleep(wait)

    raise RuntimeError(f"All {retries} attempts failed.")

# Active, running async chat loop
async def main():
    print("🤖 Interactive Async Chat Agent Started! (Type 'exit' or 'quit' to stop)")
    print("This version uses a TEMPORARY Python list in RAM for memory.")
    print("-" * 60)

    # 1. Initialize the conversation history list in RAM.
    conversation_history = [
        {"role": "system", "content": "You are a helpful and concise AI engineering instructor."}
    ]

    while True:
        # 2. Get user input in an async-friendly way
        user_input = await asyncio.to_thread(input, "\nYou: ")

        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye! Clearing RAM memory...")
            break

        if not user_input.strip():
            continue

        # 3. Append user message to active RAM list
        conversation_history.append({"role": "user", "content": user_input})

        try:
            # 4. Send the entire list history to Groq
            result = await ask_groq(conversation_history)
            print(f"\nGroq: {result}")

            # 5. Append Groq's response so it is remembered in the next turn
            conversation_history.append({"role": "assistant", "content": result})

        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
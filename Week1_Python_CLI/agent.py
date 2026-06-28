import asyncio
import os
import argparse
from dotenv import load_dotenv
from groq import AsyncGroq, RateLimitError

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found. Check your .env file.")

client = AsyncGroq(api_key=api_key)

async def ask_groq(prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                timeout=30.0
            )
            return response.choices[0].message.content

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

async def main():
    parser = argparse.ArgumentParser(description="Groq CLI Agent")
    parser.add_argument("prompt", type=str, help="Your prompt")
    args = parser.parse_args()

    try:
        result = await ask_groq(args.prompt)
        print("\nGroq:", result)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
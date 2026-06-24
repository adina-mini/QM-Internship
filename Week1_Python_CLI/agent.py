from groq import Groq
import os
import time
import argparse
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_groq(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}])
            return response.choices[0].message.content
            
        except Exception as e:
            if "429" in str(e):
                print("Rate Limiting error : Too many Requests")
                time.sleep(10)
            else:
                wait = 2 ** attempt 
                print(f"[Attempt {attempt+1}/{retries}] Error: {e} — retrying in {wait}s...")
                time.sleep(wait)
    return None

def main():
    parser =  argparse.ArgumentParser(description = "Gemini CLI Agent")
    parser.add_argument("prompt",type=str  , help="Your Prompt")
    args = parser.parse_args()
    result = ask_groq(args.prompt)
    print("\nGroq:", result)
if __name__ ==  "__main__":
    main()


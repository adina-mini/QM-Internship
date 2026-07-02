import os
import asyncio
import argparse
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

# FUNCTIONS 
async def get_weather(city: str) -> str:
    async with httpx.AsyncClient() as http:
        r = await http.get(f"https://wttr.in/{city}?format=3", timeout=10.0)
        return r.text
    
def calculate(expression: str) -> str:
    # Allow only numbers, spaces, parentheses, and math operators
    if not re.fullmatch(r"[0-9+\-*/().%\s]+", expression):
        return "Invalid mathematical expression."

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Math failed: {e}"

async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    async with httpx.AsyncClient() as http:
        # ✅ YEH API WORKING HAI
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        r = await http.get(url, timeout=10.0)
        data = r.json()
        rate = data['rates'][to_currency.upper()]
        converted = amount * rate
        return f"{amount} {from_currency.upper()} = {converted:.2f} {to_currency.upper()}"
    
# TOOL DEFINITION  
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "ONLY use this tool when user asks about weather, temperature, or climate. Do NOT use for time, timezone, or general questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "city name e.g london, bwp, tokyo"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type":"function",
        "function":{
            "name":"convert_currency",
            "description":"convert currency from one to other",
            "parameters":{
                "amount":{"type":"number","description":"Amount to convert"},
                "from_currency":{"type":"string","description":"current to be converted from e.g USD , EUR , PKR"},
                "to_currency":{"type":"string","description":"currency to converted to e.g INR , EUR"}
            },
            "required":["amount","from_currency","to_currency"]
            
                
            }
        },
    
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "evaluate a math expression",
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
    "convert_currency":convert_currency
}

# ASK_GROQ FUNCTION
async def ask_groq(prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            # first call 
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
                timeout=30.0,
            )
            tool_calls = response.choices[0].message.tool_calls
            
# LLM PICKS THE TOOL IF NEEDED
            if tool_calls:
                tool_call = tool_calls[0]
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                fn = TOOL_MAP.get(name)
                if not fn:
                    return f"unknown tool: {name}"                
                print(f" TOOL CALLED: {name} with args: {args}")

                
                result = await fn(**args) if inspect.iscoroutinefunction(fn) else fn(**args)
                print(f"TOOL RESULT: {result}")  
# SEND TOOL RESULT BACK TO LLM FOR FORMATTING
                final = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant. When you receive a tool result, always present it in a complete, natural sentence. Include all numbers, units, and relevant details explicitly. Never just repeat the tool output — convert it into a proper response. For weather: mention temperature, conditions, and location. For currency: mention original amount, converted amount, and rate. For math: mention the expression and result. Always ask if the user needs more details."},                    
                        {"role": "user", "content": prompt},                        
                        {"role": "assistant", "tool_calls": tool_calls},
                        {"role": "tool", "content": result, "tool_call_id": tool_call.id},
                    ],
                    timeout=30.0,
                )
                return final.choices[0].message.content                
            return response.choices[0].message.content
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
    parser = argparse.ArgumentParser(description="Groq Tool Calling Agent")
    parser.add_argument("prompt", type=str, help="your prompt")
    args = parser.parse_args()

    try:
        result = await ask_groq(args.prompt)
        print("\nGroq:", result)
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
import os
import re
import math
import httpx
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

search = TavilySearch(max_results=1)


@tool
@tool
def web_search(query: str) -> str:
    """Search the web for current information. Use only once per topic."""
    try:
        results = search.invoke(query)

        if not results:
            return "No results found."

        if isinstance(results, list):
            first = results[0]
            return first.get("content") or first.get("text") or str(first)

        return str(results)

    except Exception as e:
        return f"Search failed: {e}"


@tool
def save_notes(filename: str, content: str) -> str:
    """Save research notes to a file. Only call when user explicitly asks to save."""
    try:
        os.makedirs("notes", exist_ok=True)
        clean = filename.replace(".txt", "").replace("notes/", "").strip()
        path = f"notes/{clean}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Notes saved to {path}"
    except Exception as e:
        return f"Failed to save notes: {e}"


@tool
def read_file(filename: str) -> str:
    """Read a previously saved notes file. Only call when user explicitly asks to read."""
    try:
        clean = filename.replace(".txt", "").replace("notes/", "").strip()
        path = f"notes/{clean}.txt"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File '{clean}.txt' not found in notes/"
    except Exception as e:
        return f"Failed to read file: {e}"


@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression or factorial."""
    expression = expression.strip()
    if expression.endswith("!") and expression[:-1].strip().isdigit():
        return str(math.factorial(int(expression[:-1].strip())))
    if not re.fullmatch(r"[0-9+\-*/().%\s]+", expression):
        return "Invalid mathematical expression."
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Calculation failed: {e}"


@tool
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currency from one type to another."""
    try:
        async with httpx.AsyncClient() as http:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
            r = await http.get(url, timeout=10.0)
            data = r.json()
            rate = data["rates"][to_currency.upper()]
            converted = amount * rate
            return f"{amount} {from_currency.upper()} = {converted:.2f} {to_currency.upper()}"
    except KeyError:
        return f"Currency {to_currency.upper()} not found."
    except Exception as e:
        return f"Currency conversion failed: {e}"


tools = [web_search, save_notes, read_file, calculate, convert_currency]

#Tools.py
import httpx
import re
from langchain_core.tools import tool


@tool
async def get_weather(city: str) -> str:
    """Get current weather for a city"""
    async with httpx.AsyncClient() as http:
        r = await http.get(f"https://wttr.in/{city}?format=3", timeout=10.0)
        return r.text


@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression"""
    if not re.fullmatch(r"[0-9+\-*/().%\s]+", expression):
        return "Invalid mathematical expression."
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"


@tool
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currency from one type to another"""
    async with httpx.AsyncClient() as http:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        r = await http.get(url, timeout=10.0)
        data = r.json()
        rate = data["rates"][to_currency.upper()]
        converted = amount * rate
        return (
            f"{amount} {from_currency.upper()} = {converted:.2f} {to_currency.upper()}"
        )


tools = [get_weather, calculate, convert_currency]

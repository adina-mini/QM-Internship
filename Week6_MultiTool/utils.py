# UTILS.py
import os
import sys
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise ValueError("GROQ_API_KEY not found in .env")


tavily_key = os.getenv("TAVILY_API_KEY")
if not tavily_key:
    raise ValueError("TAVILY_API_KEY not found in .env")

try:
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_key, temperature=0)
except Exception as e:
    print(f"ERROR: Failed to initialize Groq client: {e}")
    sys.exit(1)

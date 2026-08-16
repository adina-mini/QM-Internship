import os
import asyncio
from tavily import TavilyClient
from dotenv import load_dotenv
from logger import logger

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.5  # doubles each retry: 1.5s, 3s, 6s


async def web_search(query: str) -> str:
    """Search the web using Tavily and return formatted results.
    Retries on transient failures (network resets, timeouts) before
    giving up — a single dropped connection shouldn't fail the whole query."""

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await asyncio.to_thread(
                tavily_client.search, query=query, max_results=3
            )
            results = response.get("results", [])

            if not results:
                return "No results found."

            formatted = []
            for res in results:
                title = res.get("title", "No title")
                content = res.get("content", "No content")
                formatted.append(f"Title: {title}\nContent: {content}\n---")

            return "\n".join(formatted)

        except Exception as e:
            last_error = e
            logger.error(f"Tavily search attempt {attempt}/{MAX_RETRIES} failed: {e}")

            if attempt < MAX_RETRIES:
                delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

    # All retries exhausted — fail honestly, don't pretend results came back.
    logger.error(f"Tavily search failed after {MAX_RETRIES} attempts: {last_error}")
    return f"Search failed after {MAX_RETRIES} attempts: {str(last_error)}"

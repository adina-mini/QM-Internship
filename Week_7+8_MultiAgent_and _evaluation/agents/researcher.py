from state import AgentState
from tools import web_search
from logger import logger


async def researcher_node(state: AgentState) -> AgentState:
    """Perform web search and store results in state."""
    query = state["query"]

    search_results = await web_search(query)

    state["research_data"] = search_results
    state["next_agent"] = "writer"

    print(f"[RESEARCHER] Retrieved {len(search_results)} chars | Next: WRITER")

    return state

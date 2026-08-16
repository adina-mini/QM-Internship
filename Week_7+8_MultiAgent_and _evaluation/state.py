from typing import List, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    next_agent: str
    query: str
    task: str
    research_data: Optional[str]
    final_answer: Optional[str]

from langgraph.graph import StateGraph, END
from state import AgentState
from agents.planner import planner_node
from agents.researcher import researcher_node
from agents.writer import writer_node


def should_continue(state: AgentState) -> str:
    """Router function to decide next node."""
    if state["next_agent"] == "FINISH":
        return END
    return state["next_agent"]


# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.set_entry_point("planner")
workflow.add_conditional_edges(
    "planner",
    should_continue,
    {"researcher": "researcher", "writer": "writer", END: END},
)
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", END)
app = workflow.compile()

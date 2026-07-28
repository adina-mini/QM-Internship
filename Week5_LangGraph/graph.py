# Graph.py
from langgraph.graph import StateGraph, START, END
from state import AgentState
from nodes import chatbot_node, tool_node


def should_continue(state: AgentState):
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


graph = StateGraph(AgentState)
graph.add_node("chatbot", chatbot_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "chatbot")
graph.add_conditional_edges("chatbot", should_continue)
graph.add_edge("tools", "chatbot")

app = graph.compile()

with open("graph.png", "wb") as f:
    f.write(app.get_graph().draw_mermaid_png())

# print("Graph saved as graph.png")

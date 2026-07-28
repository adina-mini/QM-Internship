#Nodes.py
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from state import AgentState
from utils import llm
from tools import tools

llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a helpful AI assistant.
- Respond naturally to greetings
- Use weather tool for weather questions
- Use calculate tool for math
- Use convert_currency tool for currency conversion
- Answer directly when no tool needed"""


async def chatbot_node(state: AgentState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = await llm_with_tools.ainvoke(messages)

    if getattr(response, "tool_calls", None):
        for tc in response.tool_calls:
            print(f"TOOL CALLED: {tc['name']} with args: {tc['args']}")

    return {"messages": [response]}


tool_node = ToolNode(tools)

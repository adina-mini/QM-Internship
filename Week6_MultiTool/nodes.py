from langchain_core.messages import SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
from state import AgentState
from utils import llm
from tools import tools

llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a helpful research assistant with access to external tools.

TOOLS:
- web_search: search internet for current info
- save_notes: save findings to a file
- read_file: read a saved file
- calculate: math expressions and factorials
- convert_currency: currency conversion

STRICT RULES:
- Greetings → respond directly, no tools
- web_search → use ONCE per request, use results directly
- convert_currency → call ONCE, never guess rates
- calculate → math only
- save_notes → ONLY when user says "save"
- read_file → ONLY when user says "read file"
- NEVER mix text and tool calls in same response
- NEVER call tools that are not needed
- After tool returns result → use it to answer, stop calling tools"""

async def chatbot_node(state: AgentState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    try:
        response = await llm_with_tools.ainvoke(messages)
        if getattr(response, "tool_calls", None):
            for tc in response.tool_calls:
                print(f"TOOL CALLED: {tc['name']} with args: {tc['args']}")
        return {"messages": [response]}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Something went wrong. Please rephrase your question.")]}

tool_node = ToolNode(tools)
import asyncio
from graph import app
from state import AgentState
from langchain_core.messages import HumanMessage
from logger import logger


async def main(query):
    """Run the multiagent system with user query input"""
    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "next_agent": "",
        "query": "",
        "research_data": None,
        "final_answer": None,
    }

    final_state = await app.ainvoke(initial_state)

    print(final_state["final_answer"])
    print("\n")

    logger.info(f"Final Answer: {final_state.get('final_answer', '')}")
    logger.info("Agent execution completed")


if __name__ == "__main__":
    print("MULTI AGENT SYSTEM : WEEK 7")

    while True:
        query = input("\nAsk Something (type 'exit' to quit): ")

        if query.strip().lower() == "exit":
            print("Goodbye!")
            break

        asyncio.run(main(query))

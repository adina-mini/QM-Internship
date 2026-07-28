# Main.py
import asyncio
from graph import app
from langchain_core.messages import HumanMessage


async def main():

    print("AI Agent — Week 5 LangGraph")

    while True:
        question = input("\nAsk: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            continue

        result = await app.ainvoke({"messages": [HumanMessage(content=question)]})
        print("\nAgent:", result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())

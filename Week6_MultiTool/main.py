import asyncio
from graph import app
from langchain_core.messages import HumanMessage


async def main():
    #print("\n")
    print("Research Assistant — Week 6")
    #print("\n")
    print("Tools: web search, notes, calculator, currency")
    print("Type 'exit' to quit\n")

    while True:
        question = input("Ask: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            continue

        result = await app.ainvoke({"messages": [HumanMessage(content=question)]})
        print(f"\nAgent: {result['messages'][-1].content}\n")


if __name__ == "__main__":
    asyncio.run(main())

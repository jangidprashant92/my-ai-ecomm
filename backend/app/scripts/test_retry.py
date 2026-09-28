import asyncio

from dotenv import load_dotenv

load_dotenv()

from app.ai.agents.commerce_agent import CommerceAgent
from app.ai.llm.factory import LLMFactory
from app.ai.tools.test_tools import flaky_test_tool
from langchain_core.messages import HumanMessage


async def main() -> None:
    model = LLMFactory.create()

    agent = CommerceAgent(
        model=model,
        tools=[
            flaky_test_tool,
        ],
    )

    result = await agent.agent.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=("Run the flaky_test_tool. Call the tool directly.")
                )
            ]
        }
    )

    print("\n=== FINAL RESULT ===")

    for message in result["messages"]:
        print(f"\n{type(message).__name__}")
        print(message.content)


if __name__ == "__main__":
    asyncio.run(main())

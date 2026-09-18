from app.ai.prompts.chat import CHAT_SYSTEM_PROMPT
from langchain.messages import SystemMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import MessagesState


def create_chat_node(
    model: BaseChatModel,
    tools: list,
):
    model_with_tools = model.bind_tools(tools)

    async def call_model(state: MessagesState):
        messages = [
            SystemMessage(content=CHAT_SYSTEM_PROMPT),
            *state["messages"],
        ]

        response = await model_with_tools.ainvoke(messages)

        print(response)

        tool_count = len(getattr(response, "tool_calls", []))

        return {
            "messages": [response],
            "tool_count": tool_count,
            "last_tool_name": (response.tool_calls[0]["name"] if tool_count else None),
        }

    return call_model

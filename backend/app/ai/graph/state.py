from langgraph.graph import MessagesState


class ChatState(MessagesState):
    """
    State for the main CommerceOps chatbot.

    MessagesState already provides:
    - messages
    - message reducer
    """

    intent: str | None
    tool_count: int
    last_tool_name: str | None

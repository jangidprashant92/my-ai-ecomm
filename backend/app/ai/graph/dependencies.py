from typing import Annotated, Any

from fastapi import Depends, Request


def get_chat_graph(request: Request) -> Any:
    graph = request.app.state.chat_graph

    if graph is None:
        raise RuntimeError("Chat graph is not initialized")

    return graph


ChatGraphDep = Annotated[
    Any,
    Depends(get_chat_graph),
]

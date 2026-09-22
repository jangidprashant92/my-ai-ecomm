from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.ai.graph.builder import build_chat_graph
from app.ai.llm.factory import LLMFactory
from app.ai.tools.order_tools import create_order_tools
from app.ai.tools.product_tools import create_product_tools
from app.core.config import settings
from app.core.database import create_session


def generate_graph_png(graph):
    from main import PROJECT_ROOT

    output_path = f"{PROJECT_ROOT}/docs/root_graph.png"
    graph.get_graph().draw_mermaid_png(output_file_path=output_path)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    checkpoint_path = Path(settings.LANGGRAPH_CHECKPOINT_DB)

    checkpoint_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
        await checkpointer.setup()

        model = LLMFactory.create()

        order_tools = create_order_tools(
            session_factory=create_session,
        )

        product_tools = create_product_tools(
            session_factory=create_session,
        )

        app.state.chat_graph = build_chat_graph(
            model=model,
            checkpointer=checkpointer,
            order_tools=order_tools,
            product_tools=product_tools,
            session_factory=create_session,
        )
        try:
            # Generate Graph
            generate_graph_png(app.state.chat_graph)
        except (ImportError, OSError, RuntimeError) as error:
            print(f"Image error: {error}")

        yield

        app.state.chat_graph = None

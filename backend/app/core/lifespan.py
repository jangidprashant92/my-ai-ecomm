from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.ai.agents.commerce_agent import CommerceAgent
from app.ai.graph.builder import build_chat_graph
from app.ai.llm.factory import LLMFactory
from app.ai.rag.embeddings import EmbeddingProvider
from app.ai.rag.service import RagService
from app.ai.rag.vector_store import QdrantKnowledgeStore
from app.ai.tools import create_all_tools
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

        commerce_tools = create_all_tools(
            session_factory=create_session,
        )

        commerce_agent = CommerceAgent(
            model=model,
            tools=commerce_tools,
        ).agent

        embedding_provider = EmbeddingProvider()

        vector_store = QdrantKnowledgeStore(
            embeddings=embedding_provider.embeddings,
        )

        vector_store.connect_existing()

        rag_service = RagService(
            vector_store=vector_store,
            model=model,
        )

        app.state.chat_graph = build_chat_graph(
            model=model,
            checkpointer=checkpointer,
            session_factory=create_session,
            rag_service=rag_service,
            commerce_agent=commerce_agent,
        )
        try:
            # Generate Graph
            generate_graph_png(app.state.chat_graph)
        except (ImportError, OSError, RuntimeError) as error:
            print(f"Image error: {error}")

        yield

        app.state.chat_graph = None

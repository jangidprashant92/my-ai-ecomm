from typing import Any

from langgraph.errors import GraphInterrupt
from mlflow.langchain.langchain_tracer import MlflowLangchainTracer


class HITLAwareMlflowTracer(MlflowLangchainTracer):
    """
    Treat LangGraph GraphInterrupt as normal control flow.

    GraphInterrupt is expected when HumanInTheLoopMiddleware
    pauses execution for human approval.
    """

    def on_chain_error(
        self,
        error: BaseException,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if isinstance(error, GraphInterrupt):
            run_id = kwargs.pop("run_id", None)
            inputs = kwargs.pop("inputs", None)

            if run_id is None:
                return

            self.on_chain_end(
                outputs={},
                inputs=inputs,
                run_id=run_id,
                **kwargs,
            )

            return

        super().on_chain_error(
            error,
            *args,
            **kwargs,
        )

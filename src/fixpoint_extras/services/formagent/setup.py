"""Set up the form agent workflow"""

from typing import Mapping, Optional

import fixpoint
from fixpoint.cache import SupportsChatCompletionCache
from fixpoint.agents.callbacks import TikTokenLogger
from fixpoint.agents.openai import OpenAIClients
from fixpoint.analyze.memory import DataframeMemory

from fixpoint_extras.workflows.imperative import WorkflowContext, Workflow


def setup_workflow(
    openai_key: str,
    model_name: str,
    cache: Optional[SupportsChatCompletionCache] = None,
    openai_base_url: Optional[str] = None,
    default_openai_headers: Optional[Mapping[str, str]] = None,
) -> WorkflowContext:
    """Set up the workflow context

    Set up the workflow context, which includes the workflow ojbect, the agent,
    the agent's memory store, and a logger for the workflow.
    """
    # Log token usage
    tokenlogger = TikTokenLogger(model_name)
    agent = fixpoint.agents.OpenAIAgent(
        model_name=model_name,
        openai_clients=OpenAIClients.from_api_key(
            openai_key, base_url=openai_base_url, default_headers=default_openai_headers
        ),
        memory=DataframeMemory(),
        pre_completion_fns=[tokenlogger.tiktoken_logger],
        cache=cache,
    )

    workflow_run = Workflow(id="form_filler_agent").run()

    return WorkflowContext.from_workflow(workflow_run, {"main": agent}, cache)

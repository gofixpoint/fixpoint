"""Set up the form agent workflow"""

from typing import Mapping, Optional

import fixpoint
from fixpoint.cache import SupportsChatCompletionCache
from fixpoint.agents.callbacks import TikTokenLogger
from fixpoint.agents.openai import OpenAIClients
from fixpoint.analyze.memory import DataframeMemory

from fixpoint_extras.workflows.imperative import WorkflowContext, Workflow


def get_workflow_agent(
    openai_key: str,
    model_name: str,
    cache: Optional[SupportsChatCompletionCache] = None,
    openai_base_url: Optional[str] = None,
    default_openai_headers: Optional[Mapping[str, str]] = None,
) -> fixpoint.agents.OpenAIAgent:
    """Set up the workflow context
    Set up the workflow context, which includes the workflow object, the agent,
    the agent's memory store, and a logger for the workflow.
    """
    # Log token usage
    agent = fixpoint.agents.OpenAIAgent(
        agent_id="main",
        model_name=model_name,
        openai_clients=OpenAIClients.from_api_key(
            openai_key, base_url=openai_base_url, default_headers=default_openai_headers
        ),
        memory=DataframeMemory(),
        pre_completion_fns=[TikTokenLogger(model_name).tiktoken_logger],
        cache=cache,
    )

    return agent


def setup_workflow(
    openai_key: str,
    model_name: str,
    cache: Optional[SupportsChatCompletionCache] = None,
    openai_base_url: Optional[str] = None,
    default_openai_headers: Optional[Mapping[str, str]] = None,
) -> WorkflowContext:
    """Set up the workflow context

    Set up the workflow context, which includes the workflow object, the agent,
    the agent's memory store, and a logger for the workflow.
    """
    agent = get_workflow_agent(
        openai_key, model_name, cache, openai_base_url, default_openai_headers
    )

    workflow_run = Workflow(id="form_filler_agent").run()

    return WorkflowContext(workflow_run, [agent], cache)

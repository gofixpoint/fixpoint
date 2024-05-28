"""Set up the form agent workflow"""

from dataclasses import dataclass
import logging

import fixpoint
from fixpoint.agents.protocol import TikTokenLogger
from fixpoint.agents.openai import OpenAIClients
from fixpoint.analyze.memory import DataframeMemory


@dataclass
class WorkflowContext:
    """Context for a workflow.

    Holds all relevant context for a workflow. Pass this into every step
    function of your workflow.
    """

    agent: fixpoint.agents.BaseAgent
    logger: logging.Logger
    memory: DataframeMemory
    workflow: fixpoint.workflow.SupportsWorkflow


def setup_workflow(openai_key: str) -> WorkflowContext:
    """Set up the workflow context

    Set up the workflow context, which includes the workflow ojbect, the agent,
    the agent's memory store, and a logger for the workflow.
    """
    model_name = "gpt-3.5-turbo"
    agent_mem = DataframeMemory()
    # Log token usage
    tokenlogger = TikTokenLogger(model_name)
    agent = fixpoint.agents.OpenAIAgent(
        model_name=model_name,
        openai_clients=OpenAIClients.from_api_key(openai_key),
        memory=agent_mem,
        pre_completion_fns=[tokenlogger.tiktoken_logger],
    )

    workflow = fixpoint.workflow.Workflow(display_name="form filler agent workflow")

    return WorkflowContext(
        agent=agent,
        memory=agent_mem,
        workflow=workflow,
        logger=logging.getLogger(f"fixpoint_workflow_{workflow.id}"),
    )

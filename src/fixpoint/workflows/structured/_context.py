"""The workflow context for structured workflows"""

import logging
from typing import List, Optional

from fixpoint.agents import AsyncBaseAgent
from fixpoint.cache import SupportsChatCompletionCache

from ..imperative import WorkflowContext as ImperativeWorkflowContext, WorkflowRun
from ..imperative._wrapped_workflow_agents import AsyncWrappedWorkflowAgents
from ._run_config import RunConfig


class WorkflowContext:
    """A context for a structured workflow

    A WorkflowContext tracks the current WorkflowRun, and it contains a few
    things:

    - The `workflow_run` itself, with which you can inspect the current node
      state (what task and step are we in?), store and search documents scoped to
      the workflow, and fill out structured forms scoped to the workflow.
    - The dictionary of `agents` in the workflow run. Each agent has memory for
      the life of the `WorkflowRun`.
    - An optional `cache`, which stores cached agent inference requests, so you
      don't duplicate requests and spend extra money. You can access this to
      invalidate cache items or skip caching for certain steps.
    - A logger that is scoped to the lifetime of the `WorkflowRun`.
    - The `run_config`, that defines settings for the worflow run. You rarely
      need to access this.
    """

    run_config: RunConfig
    _imp_ctx: ImperativeWorkflowContext

    def __init__(
        self,
        run_config: RunConfig,
        workflow_run: WorkflowRun,
        agents: List[AsyncBaseAgent],
        cache: Optional[SupportsChatCompletionCache] = None,
        logger: Optional[logging.Logger] = None,
        *,
        _workflow_agents_override_: Optional[AsyncWrappedWorkflowAgents] = None,
    ) -> None:
        self._imp_ctx = ImperativeWorkflowContext(
            workflow_run=workflow_run,
            cache=cache,
            logger=logger,
            # Structured workflows only support async agents, because every task
            # and step in a structured workflow is async. There is not a good
            # reason to use sync agents.
            agents=[],
            async_agents=agents,
            _async_workflow_agents_override_=_workflow_agents_override_,
        )
        self.run_config = run_config

    @property
    def agents(self) -> AsyncWrappedWorkflowAgents:
        """The agents scoped to the workflow"""
        return self._imp_ctx.async_agents

    @property
    def workflow_run(self) -> WorkflowRun:
        """The workflow run the agents run in"""
        return self._imp_ctx.workflow_run

    @property
    def cache(self) -> Optional[SupportsChatCompletionCache]:
        """The agent cache"""
        return self._imp_ctx.cache

    @property
    def logger(self) -> logging.Logger:
        """The workflow run context's logger"""
        return self._imp_ctx.logger

    def clone(
        self, new_task: str | None = None, new_step: str | None = None
    ) -> "WorkflowContext":
        """Clones the workflow context"""

        # We need to override this metod from the child class because we have
        # different init parameters.

        # clone the workflow run
        new_workflow_run = self.workflow_run.clone(new_task=new_task, new_step=new_step)
        # clone the agents
        new_agents = self.agents.clone(new_workflow_run)

        return self.__class__(
            agents=[],
            workflow_run=new_workflow_run,
            cache=self.cache,
            logger=self.logger,
            run_config=self.run_config,
            _workflow_agents_override_=new_agents,
        )

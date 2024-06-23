"""The context for a workflow"""

import logging
from typing import Dict, Optional

from fixpoint.agents import BaseAgent
from fixpoint.cache import SupportsChatCompletionCache
from fixpoint.memory import NoOpMemory, Memory
from .workflow import WorkflowRun
from ._workflow_agent import WorkflowAgent


class _WrappedWorkflowAgents:
    _agents: Dict[str, WorkflowAgent]
    _workflow_run: WorkflowRun

    def __init__(self, agents: Dict[str, BaseAgent], workflow_run: WorkflowRun) -> None:
        self._agents = self._prepare_agents(workflow_run, agents)
        self._workflow_run = workflow_run

    def __getitem__(self, key: str) -> BaseAgent:
        return self._agents[key]

    def __setitem__(self, key: str, agent: BaseAgent) -> None:
        self._agents[key] = self._wrap_agent(self._workflow_run, agent)

    def _prepare_agents(
        self, workflow_run: WorkflowRun, agents: Dict[str, BaseAgent]
    ) -> Dict[str, WorkflowAgent]:
        new_agents: Dict[str, WorkflowAgent] = {}
        for name, agent in agents.items():
            new_agents[name] = self._wrap_agent(workflow_run, agent)
        return new_agents

    def _update_agents(self, workflow_run: WorkflowRun) -> None:
        for agent in self._agents.values():
            # pylint: disable=protected-access
            agent._workflow_run = workflow_run

    def _wrap_agent(self, workflow_run: WorkflowRun, agent: BaseAgent) -> WorkflowAgent:
        # We require agents in a workflow to have working memory
        if isinstance(agent.memory, NoOpMemory):
            agent.memory = Memory()
        return WorkflowAgent(agent, workflow_run)


class WorkflowContext:
    """Context for a workflow.

    Holds all relevant context for a workflow. Pass this into every step
    function of your workflow.
    """

    agents: _WrappedWorkflowAgents
    workflow_run: WorkflowRun
    cache: Optional[SupportsChatCompletionCache]
    logger: logging.Logger

    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        workflow_run: WorkflowRun,
        cache: Optional[SupportsChatCompletionCache] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.agents = _WrappedWorkflowAgents(agents, workflow_run)
        self.workflow_run = workflow_run
        self.cache = cache
        self.logger = logger or logging.getLogger(
            f"fixpoint/workflows/runs/{workflow_run.id}"
        )

    def _update_workflow_run(self, workflow_run: WorkflowRun) -> None:
        self.workflow_run = workflow_run
        # pylint: disable=protected-access
        self.agents._update_agents(workflow_run)

    @classmethod
    def from_workflow(
        cls,
        workflow_run: WorkflowRun,
        agents: Dict[str, BaseAgent],
        cache: Optional[SupportsChatCompletionCache] = None,
    ) -> "WorkflowContext":
        """Creates a WorkflowContext for a workflow"""
        return cls(
            agents=agents,
            workflow_run=workflow_run,
            cache=cache,
            logger=logging.getLogger(f"fixpoint/workflows/runs/{workflow_run.id}"),
        )

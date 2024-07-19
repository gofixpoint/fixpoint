"""Wrapped agents scoped to a workflow run"""

__all__ = ["WrappedWorkflowAgents"]

from typing import Dict, Iterable, List, Optional, Tuple

from fixpoint.agents import BaseAgent
from fixpoint.memory import NoOpMemory, Memory
from .workflow import WorkflowRun
from ._workflow_agent import WorkflowAgent


class WrappedWorkflowAgents:
    """Wrapped agents scoped to a workflow run"""

    _agents: Dict[str, WorkflowAgent]
    _workflow_run: WorkflowRun

    def __init__(
        self,
        agents: List[BaseAgent],
        workflow_run: WorkflowRun,
        *,
        _workflow_agents_override_: Optional[Dict[str, WorkflowAgent]] = None,
    ) -> None:
        self._workflow_run = workflow_run

        if _workflow_agents_override_ is None:
            agents_dict = {agent.id: agent for agent in agents}
            if len(agents_dict) != len(agents):
                raise ValueError("Duplicate agent ids are not allowed")
            self._agents = self._prepare_agents(workflow_run, agents_dict)
        else:
            if len(_workflow_agents_override_) != len(
                {agent.id: agent for agent in _workflow_agents_override_.values()}
            ):
                raise ValueError("Duplicate agent ids are not allowed")
            self._agents = _workflow_agents_override_

    def __getitem__(self, key: str) -> BaseAgent:
        return self._agents[key]

    def __setitem__(self, key: str, agent: BaseAgent) -> None:
        self._agents[key] = self._wrap_agent(self._workflow_run, agent)

    def keys(self) -> Iterable[str]:
        """Returns the agent ids in the workflow"""
        return self._agents.keys()

    def values(self) -> Iterable[BaseAgent]:
        """Returns the agents in the workflow"""
        return self._agents.values()

    def items(self) -> Iterable[Tuple[str, BaseAgent]]:
        """Returns the (agent ids, agents) in the workflow"""
        return self._agents.items()

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
            if workflow_run.storage_config:
                agent.memory = workflow_run.storage_config.memory_factory(agent.id)
            else:
                agent.memory = Memory()
        return WorkflowAgent(agent, workflow_run)

    def clone(
        self, new_workflow_run: Optional[WorkflowRun] = None
    ) -> "WrappedWorkflowAgents":
        """Clones the workflow context"""
        workflow_run = self._workflow_run
        if new_workflow_run:
            workflow_run = new_workflow_run
        new_agents = {
            # pylint: disable=protected-access
            k: WorkflowAgent(v._inner_agent, workflow_run)
            for k, v in self._agents.items()
        }

        new_self = self.__class__(
            agents=[],
            workflow_run=workflow_run,
            _workflow_agents_override_=new_agents,
        )
        if new_workflow_run:
            # pylint: disable=protected-access
            new_self._update_agents(workflow_run)
        return new_self

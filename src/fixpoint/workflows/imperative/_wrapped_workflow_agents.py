"""Wrapped agents scoped to a workflow run"""

__all__ = ["WrappedWorkflowAgents", "AsyncWrappedWorkflowAgents"]

from dataclasses import dataclass
from typing import cast, Dict, Iterable, List, Optional, Tuple, TypeVar, Union

from fixpoint.agents import BaseAgent, AsyncBaseAgent
from fixpoint.memory import NoOpMemory, Memory
from .workflow import WorkflowRun
from ._workflow_agent import WorkflowAgent, AsyncWorkflowAgent


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
        self._agents = cast(
            Dict[str, WorkflowAgent],
            _init_agents(
                workflow_run, _SyncInitArgs(agents, _workflow_agents_override_)
            ),
        )

    def __getitem__(self, key: str) -> BaseAgent:
        return self._agents[key]

    def __setitem__(self, key: str, agent: BaseAgent) -> None:
        self._agents[key] = _wrap_sync_agent(self._workflow_run, agent)

    def keys(self) -> Iterable[str]:
        """Returns the agent ids in the workflow"""
        return self._agents.keys()

    def values(self) -> Iterable[BaseAgent]:
        """Returns the agents in the workflow"""
        return self._agents.values()

    def items(self) -> Iterable[Tuple[str, BaseAgent]]:
        """Returns the (agent ids, agents) in the workflow"""
        return self._agents.items()

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
            _update_agents(new_self._agents, workflow_run)
        return new_self


class AsyncWrappedWorkflowAgents:
    """Wrapped async agents scoped to a workflow run"""

    _agents: Dict[str, AsyncWorkflowAgent]
    _workflow_run: WorkflowRun

    def __init__(
        self,
        agents: List[AsyncBaseAgent],
        workflow_run: WorkflowRun,
        *,
        _workflow_agents_override_: Optional[Dict[str, AsyncWorkflowAgent]] = None,
    ) -> None:
        self._workflow_run = workflow_run
        self._agents = cast(
            Dict[str, AsyncWorkflowAgent],
            _init_agents(
                workflow_run, _AsyncInitArgs(agents, _workflow_agents_override_)
            ),
        )

    def __getitem__(self, key: str) -> AsyncBaseAgent:
        return self._agents[key]

    def __setitem__(self, key: str, agent: AsyncBaseAgent) -> None:
        self._agents[key] = _wrap_async_agent(self._workflow_run, agent)

    def keys(self) -> Iterable[str]:
        """Returns the agent ids in the workflow"""
        return self._agents.keys()

    def values(self) -> Iterable[AsyncBaseAgent]:
        """Returns the agents in the workflow"""
        return self._agents.values()

    def items(self) -> Iterable[Tuple[str, AsyncBaseAgent]]:
        """Returns the (agent ids, agents) in the workflow"""
        return self._agents.items()

    def clone(
        self, new_workflow_run: Optional[WorkflowRun] = None
    ) -> "AsyncWrappedWorkflowAgents":
        """Clones the workflow context"""
        workflow_run = self._workflow_run
        if new_workflow_run:
            workflow_run = new_workflow_run
        new_agents = {
            # pylint: disable=protected-access
            k: AsyncWorkflowAgent(v._inner_agent, workflow_run)
            for k, v in self._agents.items()
        }

        new_self = self.__class__(
            agents=[],
            workflow_run=workflow_run,
            _workflow_agents_override_=new_agents,
        )
        if new_workflow_run:
            # pylint: disable=protected-access
            _update_agents(new_self._agents, workflow_run)
        return new_self


GenAgent = TypeVar("GenAgent", bound=Union[BaseAgent, AsyncBaseAgent])
GenWorkflowAgent = TypeVar(
    "GenWorkflowAgent", bound=Union[WorkflowAgent, AsyncWorkflowAgent]
)


@dataclass
class _SyncInitArgs:
    agents: List[BaseAgent]
    workflow_agents_override: Optional[Dict[str, WorkflowAgent]]


@dataclass
class _AsyncInitArgs:
    agents: List[AsyncBaseAgent]
    workflow_agents_override: Optional[Dict[str, AsyncWorkflowAgent]]


def _init_agents(
    workflow_run: WorkflowRun, init_args: Union[_SyncInitArgs, _AsyncInitArgs]
) -> Union[Dict[str, WorkflowAgent], Dict[str, AsyncWorkflowAgent]]:
    if init_args.workflow_agents_override:
        _check_unique_ids(list(init_args.workflow_agents_override.keys()))
        return init_args.workflow_agents_override

    _check_unique_ids([agent.id for agent in init_args.agents])
    if isinstance(init_args, _SyncInitArgs):
        new_sync_agents: Dict[str, WorkflowAgent] = {}
        for agent in init_args.agents:
            new_sync_agents[agent.id] = _wrap_sync_agent(workflow_run, agent)
        return new_sync_agents
    else:
        new_async_agents: Dict[str, AsyncWorkflowAgent] = {}
        for async_agent in init_args.agents:
            new_async_agents[async_agent.id] = _wrap_async_agent(
                workflow_run, async_agent
            )
        return new_async_agents


def _check_unique_ids(agent_ids: List[str]) -> None:
    if len(agent_ids) != len(set(agent_ids)):
        raise ValueError("Duplicate agent ids are not allowed")


def _wrap_sync_agent(workflow_run: WorkflowRun, agent: BaseAgent) -> WorkflowAgent:
    agent = _prepare_wrapped_agent(workflow_run, agent)
    return WorkflowAgent(agent, workflow_run)


def _wrap_async_agent(
    workflow_run: WorkflowRun, agent: AsyncBaseAgent
) -> AsyncWorkflowAgent:
    agent = _prepare_wrapped_agent(workflow_run, agent)
    return AsyncWorkflowAgent(agent, workflow_run)


def _prepare_wrapped_agent(workflow_run: WorkflowRun, agent: GenAgent) -> GenAgent:
    # We require agents in a workflow to have working memory
    if isinstance(agent.memory, NoOpMemory):
        if workflow_run.storage_config:
            agent.memory = workflow_run.storage_config.memory_factory(agent.id)
        else:
            agent.memory = Memory()
    return agent


def _update_agents(
    agents: Union[Dict[str, WorkflowAgent], Dict[str, AsyncWorkflowAgent]],
    workflow_run: WorkflowRun,
) -> None:
    for agent in agents.values():
        # pylint: disable=protected-access
        agent._workflow_run = workflow_run

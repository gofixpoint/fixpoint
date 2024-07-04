from typing import List

from fixpoint.cache import ChatCompletionTLRUCache
from fixpoint.agents import BaseAgent
from fixpoint.agents.mock import MockAgent, new_mock_completion
from fixpoint.workflows import imperative
from fixpoint.workflows.imperative.workflow_context import (
    _WrappedWorkflowAgents,
    WorkflowContext,
)
from fixpoint.workflows.imperative._workflow_agent import WorkflowAgent


class TestWrappedWorkflowAgents:
    def test_clone(self) -> None:
        agent1 = MockAgent(completion_fn=new_mock_completion, agent_id="agent1")
        agent2 = MockAgent(completion_fn=new_mock_completion, agent_id="agent2")

        workflow = imperative.Workflow(id="test_workflow")
        workflow_run = workflow.run()
        agents: List[BaseAgent] = [agent1, agent2]

        wrapped_agents = _WrappedWorkflowAgents(
            agents=agents, workflow_run=workflow_run
        )
        pre_cloned_agents = wrapped_agents._agents
        pre_cloned_workflow_run = wrapped_agents._workflow_run
        assert wrapped_agents._workflow_run == workflow_run
        assert wrapped_agents._workflow_run is workflow_run

        new_wrapped_agents = wrapped_agents.clone()

        # Clone has new agents dict, and preserves old agents.
        # The dict has the same agent IDs, with the same inner agents, but we've re-wrapped them
        assert set(wrapped_agents.keys()) == set(new_wrapped_agents.keys())
        for agent_id in wrapped_agents.keys():
            wrapped_agent = wrapped_agents[agent_id]
            new_wrapped_agent = new_wrapped_agents[agent_id]
            assert isinstance(wrapped_agent, WorkflowAgent)
            assert isinstance(new_wrapped_agent, WorkflowAgent)
            assert wrapped_agent._workflow_run is new_wrapped_agent._workflow_run
            assert wrapped_agent._inner_agent is new_wrapped_agent._inner_agent
            assert wrapped_agents[agent_id] is not new_wrapped_agents[agent_id]
        # but they are different variables
        assert new_wrapped_agents._agents is not wrapped_agents._agents
        assert wrapped_agents._agents is pre_cloned_agents

        # new agents dict should be WorkflowAgent, without accidentally
        # double-nesting another WorkflowAgent
        for agent in new_wrapped_agents.values():
            assert isinstance(agent, WorkflowAgent)
            assert not isinstance(agent._inner_agent, WorkflowAgent)

        # we didn't pass in a new workflow run, so that stays the same
        assert wrapped_agents._workflow_run is pre_cloned_workflow_run
        assert new_wrapped_agents._workflow_run is wrapped_agents._workflow_run

        # if we pass in a new workflow run, all wrapped agents should be updated
        # to refer to that new run
        new_workflow_run = workflow.run()
        wrapped_with_new_run = wrapped_agents.clone(new_workflow_run=new_workflow_run)
        assert wrapped_with_new_run._workflow_run is new_workflow_run
        assert wrapped_with_new_run._workflow_run != wrapped_agents._workflow_run
        assert wrapped_agents._workflow_run is pre_cloned_workflow_run

        for agent in wrapped_with_new_run.values():
            assert isinstance(agent, WorkflowAgent)
            assert agent._workflow_run is new_workflow_run
        # original agents do not change
        for agent in wrapped_agents.values():
            assert isinstance(agent, WorkflowAgent)
            assert agent._workflow_run == pre_cloned_workflow_run


class TestWorkflowContext:
    def test_clone(self) -> None:
        agent1 = MockAgent(completion_fn=new_mock_completion, agent_id="agent1")
        agent2 = MockAgent(completion_fn=new_mock_completion, agent_id="agent2")
        workflow = imperative.Workflow(id="test_workflow")
        workflow_run = workflow.run()
        agents: List[BaseAgent] = [agent1, agent2]
        cache = ChatCompletionTLRUCache(maxsize=1000, ttl_s=10)
        wfctx = WorkflowContext(agents=agents, workflow_run=workflow_run, cache=cache)

        new_wfctx = wfctx.clone()

        # agents should be cloned
        assert [
            agent._inner_agent
            for agent in new_wfctx.agents.values()
            if isinstance(agent, WorkflowAgent)
        ] == agents
        assert new_wfctx.agents is not wfctx.agents

        # workflow_run should be cloned
        assert new_wfctx.workflow_run == workflow_run
        assert new_wfctx.workflow_run is not wfctx.workflow_run

        # cache and logger are preserved
        assert new_wfctx.cache is cache
        assert new_wfctx.logger is wfctx.logger

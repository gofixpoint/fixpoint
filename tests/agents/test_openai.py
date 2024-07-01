import pytest

from fixpoint.agents import OpenAIAgent
from fixpoint.agents.openai import OpenAIClients


def test_openai_agent_bad_model_instantiation() -> None:
    # Check that if an invalid model is passed in then a ValueError is raised
    with pytest.raises(ValueError):
        OpenAIAgent("agent-id-1", "bad-model", OpenAIClients.from_api_key("api-key"))
    # Check that if None is passed in then a ValueError is raised
    with pytest.raises(ValueError):
        OpenAIAgent("agent-id-2", None, OpenAIClients.from_api_key("api-key"))  # type: ignore


def test_openai_agent_valid_model_instantiation() -> None:
    # Instantiate an agent
    agent = OpenAIAgent(
        agent_id="agent-id-1",
        model_name="gpt-3.5-turbo",
        openai_clients=OpenAIClients.from_api_key("api-key"),
    )

    # Check that the agent contains the model
    assert agent.model_name == "gpt-3.5-turbo"

    # Now check that the open ai methods are exposed. Check that chat exists on the agent.
    assert hasattr(agent, "chat")

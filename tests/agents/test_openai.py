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

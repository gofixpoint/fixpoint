from typing import Any
from unittest.mock import patch

import pytest
from openai.types.chat.chat_completion import (
    Choice as CompletionChoice,
    ChatCompletion as OpenAIChatCompletion,
)

import fixpoint
from fixpoint.agents.openai import OpenAIClients
from fixpoint._utils.completions import decorate_instructor_completion_with_fixp
from fixpoint.agents.mock import new_mock_orig_completion
from tests.test_utils import SampleStructure


class TestAgents:
    def test_openai_agent_bad_model_instantiation(self) -> None:
        # Check that if an invalid model is passed in then a ValueError is raised
        with pytest.raises(ValueError):
            fixpoint.agents.OpenAI("bad-model", OpenAIClients.from_api_key("api-key"))
        # Check that if None is passed in then a ValueError is raised
        with pytest.raises(ValueError):
            fixpoint.agents.OpenAI(None, OpenAIClients.from_api_key("api-key"))  # type: ignore

    def test_openai_agent_valid_model_instantiation(self) -> None:
        # Instantiate an agent
        agent = fixpoint.agents.OpenAI(
            model_name="gpt-3.5-turbo",
            openai_clients=OpenAIClients.from_api_key("api-key"),
        )

        # Check that the agent contains the model
        assert agent.fixp.model_name == "gpt-3.5-turbo"

        # Now check that the open ai methods are exposed. Check that chat exists on the agent.
        assert hasattr(agent, "chat")

    def test_openai_agent_completions_proxy(self) -> None:
        # Instantiate an agent
        agent = fixpoint.agents.OpenAI(
            model_name="gpt-3.5-turbo",
            openai_clients=OpenAIClients.from_api_key("api-key"),
        )

        def instructed_chat_completion(
            messages: Any, response_model: Any
        ) -> tuple[SampleStructure, OpenAIChatCompletion]:
            completion = new_mock_orig_completion("I'm doing good.")
            structure = SampleStructure(name="John")

            # Return in order instructor expects them
            return structure, completion

        decorated_method = decorate_instructor_completion_with_fixp(
            instructed_chat_completion
        )

        # mock the chat.completions.create method with a decorated test method to simulate a completion action
        with patch.object(
            agent.chat.completions, "create", decorated_method
        ) as mock_method:

            # Now call the chat method and check that the completion is correct
            response = agent.chat.completions.create(
                messages=[
                    {"role": "user", "content": "Hello, how are you?"},
                ],
                response_model=SampleStructure,
            )

            assert response.choices[0].message.content == "I'm doing good."
            assert response.fixp.structured_output is not None
            assert isinstance(response.fixp.structured_output, SampleStructure)
            assert response.fixp.structured_output.name == "John"

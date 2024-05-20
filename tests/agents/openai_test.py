import unittest
from unittest.mock import patch
import fixpoint

from fixpoint.utils.completions import decorate_instructor_completion_with_fixp
from tests.test_utils import SampleCompletion, SampleStructure


class TestAgents(unittest.TestCase):

    def test_openai_agent_bad_model_instantiation(self) -> None:
        # Check that if an invalid model is passed in then a ValueError is raised
        self.assertRaises(
            ValueError, fixpoint.agents.OpenAIAgent, "bad-model", "api-key"
        )
        # Check that if None is passed in then a ValueError is raised
        self.assertRaises(ValueError, fixpoint.agents.OpenAIAgent, None, "api-key")

    def test_openai_agent_valid_model_instantiation(self) -> None:
        # Instantiate an agent
        agent = fixpoint.agents.OpenAIAgent(
            model_name="gpt-3.5-turbo", api_key="api-key"
        )

        # Check that the agent contains the model
        self.assertEqual(agent.model_name, "gpt-3.5-turbo")

        # Now check that the open ai methods are exposed. Check that chat exists on the agent.
        self.assertTrue(hasattr(agent, "chat"))

    def test_openai_agent_completions_proxy(self) -> None:
        # Instantiate an agent
        agent = fixpoint.agents.OpenAIAgent(
            model_name="gpt-3.5-turbo", api_key="api-key"
        )

        def instructed_chat_completion(
            prompt: str, response_type: SampleStructure
        ) -> tuple[SampleStructure, SampleCompletion]:
            completion = SampleCompletion(prompt, "I'm doing good.")
            structure = SampleStructure("John")

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
                "Hello, how are you?", SampleStructure
            )

            # Check that the completion is correct
            self.assertEqual(response.prompt, "Hello, how are you?")
            self.assertEqual(response.output_message, "I'm doing good.")
            self.assertEqual(response.fixp.structured_output.name, "John")

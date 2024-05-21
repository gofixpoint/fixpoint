import unittest
import fixpoint


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

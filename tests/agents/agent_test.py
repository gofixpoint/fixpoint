import unittest
import fixpoint


class TestAgents(unittest.TestCase):

    def test_generic_agent_bad_model_instantiation(self) -> None:
        # Check that if an invalid model is passed in then a ValueError is raised
        self.assertRaises(ValueError, fixpoint.agents.Agent, "bad-model")
        # Check that if None is passed in then a ValueError is raised
        self.assertRaises(ValueError, fixpoint.agents.Agent, None)
        # Check that if a valid model is passed as a string that a ValueError is raised
        # since only instances of models should be passed
        self.assertRaises(ValueError, fixpoint.agents.Agent, "gpt-3.5-turbo")

    def test_generic_agent_valid_model_instantiation(self) -> None:
        # Instantiate an agent
        model = fixpoint.models.OpenAI("gpt-3.5-turbo", "api-key")
        agent = fixpoint.agents.Agent(model=model)

        # Check that the agent contains the model
        self.assertEqual(agent.model, model)

        # Now check that the open ai methods are exposed. Check that chat exists on the agent.
        self.assertTrue(hasattr(agent, "chat"))

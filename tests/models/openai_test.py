import unittest
import fixpoint


class TestOpenAIModels(unittest.TestCase):

    def test_supported_models(self) -> None:
        # Some supported models that should initialize correctly are gpt-3.5-turbo and gpt-4
        # Check that the model is initialized correctly
        model = fixpoint.models.OpenAI("gpt-3.5-turbo")
        self.assertEqual(model.model_name, "gpt-3.5-turbo")
        model = fixpoint.models.OpenAI("gpt-4")
        self.assertEqual(model.model_name, "gpt-4")

    def test_unsupported_models(self) -> None:
        # Check that if invalid values are passed in then a ValueError is raised
        self.assertRaises(ValueError, fixpoint.models.OpenAI, "invalid-model-name")

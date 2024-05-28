import pytest
import fixpoint


class TestOpenAIModels:

    def test_supported_models(self) -> None:
        # Some supported models that should initialize correctly are gpt-3.5-turbo and gpt-4
        # Check that the model is initialized correctly
        model = fixpoint.models.OpenAI("gpt-3.5-turbo", "api-key")
        assert model.model_name == "gpt-3.5-turbo"
        model = fixpoint.models.OpenAI("gpt-4", "api-key")
        assert model.model_name == "gpt-4"

    def test_unsupported_models(self) -> None:
        # Check that if invalid values are passed in then a ValueError is raised
        with pytest.raises(ValueError):
            fixpoint.models.OpenAI("invalid-model-name", "api-key")

    def test_no_api_key(self) -> None:
        # Check that if no API key is passed in then a ValueError is raised
        with pytest.raises(ValueError):
            fixpoint.models.OpenAI("gpt-3.5-turbo", None)  # type: ignore

        with pytest.raises(ValueError):
            fixpoint.models.OpenAI("gpt-4", None)  # type: ignore

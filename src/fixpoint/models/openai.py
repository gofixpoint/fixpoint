"""
This is the OpenAI module.
"""

from typing import get_args
import openai


class OpenAI:
    """
    This is the OpenAI class.
    """

    def __init__(self, model_name: str, api_key: str) -> None:
        supported_models = get_args(openai.types.ChatModel)
        if model_name not in supported_models:
            raise ValueError(
                f"Invalid model name: {model_name}. Supported models are: {supported_models}"
            )
        if api_key is None:
            raise ValueError("API key must be provided to use OpenAI models.")
        self.model_name = model_name
        self._api_key = api_key

        # Used for instantiationg an agent
        self._client_class = openai.OpenAI

    def instantiate_client(self) -> openai.OpenAI:
        """
        Instantiate the OpenAI client.
        """
        return self._client_class(api_key=self._api_key)

"""
This module contains the OpenAIAgent class, which is responsible for handling the
interaction between the user and OpenAI.
"""

from typing import Any, get_args

import openai


class OpenAIAgent:
    """
    This is the Agent class.
    """

    def __init__(self, model_name: str, api_key: str) -> None:
        # if instance of models is not one of the supported models, raise ValueError
        supported_models = get_args(openai.types.ChatModel)
        if model_name not in supported_models:
            raise ValueError(
                f"Invalid model name: {model_name}. Supported models are: {supported_models}"
            )
        if api_key is None:
            raise ValueError("API key must be provided to use OpenAI models.")
        self.model_name = model_name
        self._client = openai.OpenAI(api_key=api_key)

    def __getattr__(self, name: str) -> Any:
        # Delegate all other attributes to the client code
        return getattr(self._client, name)

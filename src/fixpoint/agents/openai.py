"""
This module contains the OpenAIAgent class, which is responsible for handling the
interaction between the user and OpenAI.
"""

from typing import Any, get_args

import openai
import instructor

from .._utils.completions import decorate_instructor_completion_with_fixp


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

        # Wrap the openai client with instructor
        self._client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        # Replace call to chat.completions.create with
        # chat.completions.create_with_completion which will expose
        # the response object and the original response
        decorated_method = decorate_instructor_completion_with_fixp(
            self._client.chat.completions.create_with_completion
        )

        setattr(self._client.chat.completions, "create", decorated_method)

    def __getattr__(self, name: str) -> Any:
        # Forward attribute access to the underlying client
        return getattr(self._client, name)

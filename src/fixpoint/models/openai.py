"""
This is the OpenAI module.
"""

from typing import get_args
from openai import types


class OpenAI:
    """
    This is the OpenAI class.
    """

    def __init__(self, model_name: str):
        supported_models = get_args(types.ChatModel)
        if model_name not in supported_models:
            raise ValueError(
                f"Invalid model name: {model_name}. Supported models are: {supported_models}"
            )
        self.model_name = model_name

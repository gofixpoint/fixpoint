"""
This module contains the Agent class, which is responsible for handling the
interaction between the user and the model.
"""

from typing import Union, Any
from fixpoint import models

_supported_models = [models.OpenAI]
SupportedModels = Union[models.OpenAI]


class Agent:
    """
    This is the Agent class.
    """

    def __init__(self, model: SupportedModels) -> None:
        # if instance of models is not one of the supported models, raise ValueError
        if not any(isinstance(model, m) for m in _supported_models):
            raise ValueError(
                f"Invalid model: {model}. Supported models are: {_supported_models}"
            )

        self.model = model
        self._client = model.instantiate_client()

    def __getattr__(self, name: str) -> Any:
        # Delegate all other attributes to the client code
        return getattr(self._client, name)

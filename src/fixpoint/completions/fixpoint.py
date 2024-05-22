"""
Completions module for the fixpoint package.
"""

from typing import Any
import openai


class FixpointCompletion:
    """
    A class that wraps a completion with a Fixpoint completion.
    """

    class Fixp:
        """
        A class that represents a Fixpoint completion.
        """

        def __init__(self, structured_output: Any) -> None:
            self.structured_output = structured_output

    def __init__(
        self, original_completion: openai.types.Completion, structured_output: Any
    ) -> None:
        self._original_completion = original_completion
        self.fixp = FixpointCompletion.Fixp(structured_output)

    def __getattr__(self, name: str) -> Any:

        if name == "fixp":
            return self.fixp

        # Forward attribute access to the underlying client
        return getattr(self._original_completion, name)

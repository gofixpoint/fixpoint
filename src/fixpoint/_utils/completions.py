"""
Utilities for completions.
"""

from typing import Callable, Any
from functools import wraps
from ..completions import ChatCompletion


def decorate_instructor_completion_with_fixp(
    func: Callable[..., Any]
) -> Callable[..., Any]:
    """
    Decorate the completion method to replace the original
    completion object with our Fixpoint ChatCompletion.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Make a call to get structured output + original completion
        structured_output, completion = func(*args, **kwargs)

        # Wrap the completion object with Fixpoint ChatCompletion and
        # inject additional information under .fixp attribute
        fixpoint_completion = ChatCompletion.from_original_completion(
            completion, structured_output
        )

        # Return fixpoint completion object
        return fixpoint_completion

    return wrapper

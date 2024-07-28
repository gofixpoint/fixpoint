"""Internal errors for structured workflows."""

from .errors import StructuredException


class InternalExecutionError(StructuredException):
    """Indicate an execution error, without full workflow context.

    When we raise an execution error inside our code, we might not have access
    to all of the info about the running workflow. We don't want to have to pass
    that info around anywhere we might raise an ExecutionError, so we have an
    internal-only version of that error that doesn't require any extra info.

    The InternalExecutionError should be transformed into an ExecutionError
    before being returned to the user.
    """

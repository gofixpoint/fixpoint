"""Error and exception definitions for structured workflows."""

__all__ = [
    "StructuredException",
    "DefinitionError",
    "ExecutionError",
    "InternalError",
]

from fixpoint.errors import FixpointException


class StructuredException(FixpointException):
    """The base class for all structured workflow exceptions."""


class DefinitionError(StructuredException):
    """Raised when there is an error in the definition of a structured workflow

    The DefinitionException is raised when defining an invalid structured
    workflow, task, or step. It can also be raised when we begin executing an
    ill-defined workflow, task, or step. It does not mean that computation
    raised an exception, but rather that the structure of your workflow program
    is wrong.
    """


class ExecutionError(StructuredException):
    """Raised when there is an error in the execution of a structured workflow

    The ExecutionException is raised when calling a structured workflow, task, or
    step incorrectly.
    """

    workflow_id: str
    workflow_run_id: str
    run_attempt_id: str

    def __init__(
        self, msg: str, workflow_id: str, workflow_run_id: str, run_attempt_id: str
    ) -> None:
        super().__init__(msg)
        self.workflow_id = workflow_id
        self.workflow_run_id = workflow_run_id
        self.run_attempt_id = run_attempt_id


class InternalError(StructuredException):
    """An internal error (non-user) in the structured workflows library"""

"""Error and exception definitions for structured workflows."""


class DefinitionException(Exception):
    """Raised when there is an error in the definition of a structured workflow

    The DefinitionException is raised when defining an invalid structured
    workflow, task, or step. It can also be raised when we begin executing an
    ill-defined workflow, task, or step. It does not mean that computation
    raised an exception, but rather that the structure of your workflow program
    is wrong.
    """


class CallException(Exception):
    """Raised when there is an error in the call of a structured workflow

    The CallException is raised when calling a structured workflow, task, or
    step incorrectly.
    """


class InternalException(Exception):
    """An internal error (non-user) in the structured workflows library"""

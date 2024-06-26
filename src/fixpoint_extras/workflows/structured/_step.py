"""Structured workflows: step definitions

In a structured workflow, a step is the smallest unit of work in a workflow.
Each step is checkpointed, so if the step fails you can resume without losing
computed work.

You can call steps from the workflow, or from tasks, but not from other steps.
Within a workflow, the step returns control to the task or workflow after being
called, which can then coordinate the next step or task in the workflow.

In a workflow, agents are able to recall memories, documents, and forms from
past or current steps and tasks.
"""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, cast

from ._context import WorkflowContext
from .errors import DefinitionException
from ._helpers import validate_func_has_context_arg, Params, Ret


class StepFixp:
    """The internal Fixpoint attribute for a step function"""

    id: str

    def __init__(self, id: str):  # pylint: disable=redefined-builtin
        self.id = id


def step(
    id: str,  # pylint: disable=redefined-builtin
) -> Callable[[Callable[Params, Ret]], Callable[Params, Ret]]:
    """Decorate a function to mark it as a step definition

    A step definition is a function that represents a step in a workflow. The
    function must have at least one argument, which is the WorkflowContext.

    An example:

    ```
    @structured.step(id="my-step")
    def my_step(ctx: WorkflowContext, args: Dict[str, Any]) -> None:
        ...
    ```
    """

    def decorator(func: Callable[Params, Ret]) -> Callable[Params, Ret]:
        # pylint: disable=protected-access
        func.__fixp = StepFixp(id)  # type: ignore[attr-defined]

        validate_func_has_context_arg(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Ret:
            print("Before calling", func.__name__)
            result = func(*args, **kwargs)
            print("After calling", func.__name__)
            return result

        return cast(Callable[Params, Ret], wrapper)

    return decorator


def get_step_fixp(fn: Callable[..., Any]) -> Optional[StepFixp]:
    """Get the internal step Fixpoint attribute for a function"""
    if not callable(fn):
        return None
    attr = getattr(fn, "__fixp", None)
    if isinstance(attr, StepFixp):
        return attr
    return None


def call_step(
    ctx: WorkflowContext,
    fn: Callable[Params, Ret],
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Ret:
    """Execute a step in a workflow.

    You must call `call_step` from within a structured workflow definition or a
    structured task definition. ie from a class decorated with
    `@structured.workflow(...)` or with `@structured.task(...)`.

    You cannot use `call_step` from within another step. `call_step` must be
    called either from the workflow or task, which coordinates the steps.

    A more complete example:

    ```
    @structured.workflow(id="my-workflow")
    class MyWorkflow:
        @structured.workflow_entrypoint()
        def main(self, ctx: WorkflowContext, args: Dict[str, Any]) -> None:
            ####
            # this is the `call_step` invocation
            structured.call_step(ctx, my_step, args[{"somevalue": "foobar"}])

    @structured.step(id="my-step")
    def my_step(ctx: WorkflowContext, args: Dict[str, Any]) -> None:
        ...
    ```
    """
    args = args or []
    kwargs = kwargs or {}

    step_fixp = get_step_fixp(fn)
    if not step_fixp:
        raise DefinitionException(f"Step {fn.__name__} is not a valid step definition")

    ret = fn(ctx, *args, **kwargs)  # type: ignore[arg-type]
    return ret

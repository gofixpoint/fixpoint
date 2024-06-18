import pytest
from fixpoint_extras.workflows import structured


def test_at_least_ctx_arg() -> None:
    @structured.task(id="mytask")
    def mytask(ctx: structured.WorkflowContext) -> None:
        pass

    with pytest.raises(structured.DefinitionError):
        @structured.task(id="myinvalidtask")
        def myinvalidtask() -> None:
            pass

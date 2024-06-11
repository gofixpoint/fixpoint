from typing import List, Optional

from pydantic import BaseModel
from fixpoint_extras.workflows.imperative.workflow import Workflow
from fixpoint_extras.workflows.imperative.form import Form


class TestForms:

    def test_workflow_forms(self) -> None:
        workflow = Workflow(
            id="test_workflow",
        )
        assert workflow.id == "test_workflow"

        run = workflow.run()
        assert run.id is not None

        class Foo(BaseModel):
            foo: Optional[str] = None
            bar: Optional[int] = None

        # Store the form on the run
        stored_form = run.forms.store(
            form_id="foo",
            schema=Foo,
            path="/foo",
            metadata={"foo": "bar"},
        )
        assert isinstance(stored_form, Form)
        assert stored_form.id == "foo"
        assert stored_form.path == "/foo"
        assert stored_form.metadata == {"foo": "bar"}

        # Retrieved form from run with id
        retrieved_form = run.forms.get(form_id="foo")
        assert isinstance(retrieved_form, Form)
        assert retrieved_form.id == "foo"
        assert retrieved_form.path == "/foo"
        assert retrieved_form.metadata == {"foo": "bar"}

        # Updated form
        updated_form: Form[Foo] = run.forms.update(
            form_id="foo", contents={"foo": "zar"}, metadata={"mymeta": "data is here!"}
        )
        assert isinstance(updated_form, Form)
        assert updated_form.id == "foo"
        # path is not updated
        assert updated_form.path == "/foo"
        assert updated_form.contents.model_dump() == {"foo": "zar", "bar": None}
        assert updated_form.metadata == {"mymeta": "data is here!"}

        # List forms
        listed_forms = run.forms.list()
        print(listed_forms)
        assert isinstance(listed_forms, List)
        assert len(listed_forms) == 1
        assert isinstance(listed_forms[0], Form)
        assert listed_forms[0].id == "foo"
        assert listed_forms[0].path == "/foo"
        assert listed_forms[0].metadata == {"mymeta": "data is here!"}

    def test_workflow_forms_with_storage(self) -> None:
        pass

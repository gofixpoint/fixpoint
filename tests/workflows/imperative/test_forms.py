from typing import Any, Dict, List, Optional, Tuple, Union, cast
import json
import pytest
from pydantic import BaseModel, Field

from fixpoint.workflows.imperative.workflow import Workflow
from fixpoint.workflows.imperative.form import Form, _is_valid_field_annotation
from fixpoint.workflows.imperative.config import create_form_supabase_storage

from tests.supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


class TicketOrderForm(BaseModel):
    name: Optional[str] = Field(
        default=None, description="The name of the ticketholder"
    )
    age: Optional[int] = Field(default=None, description="The age of the ticketholder")
    ticket_cost: Optional[float] = None
    email: Optional[str] = Field(
        default=None, description="The email of the ticketholder"
    )


class TestForms:
    def test_validate_form_schema(self) -> None:
        class WithoutOptional(BaseModel):
            name: str
            age: Optional[int] = None

        with pytest.raises(Exception):
            Form[WithoutOptional](
                id="myform",
                workflow_run_id="myworkflowrun",
                workflow_id="myworkflow",
                form_schema=WithoutOptional,
            )

        class WithInvalidComplex(BaseModel):
            names: Optional[List[str]] = None
            age: Optional[int] = None

        with pytest.raises(Exception):
            Form[WithInvalidComplex](
                id="myform",
                workflow_run_id="myworkflowrun",
                workflow_id="myworkflow",
                form_schema=WithInvalidComplex,
            )

        class WithValid(BaseModel):
            name: Optional[str] = None
            age: Optional[int] = None

        class WithValidField(BaseModel):
            name: Optional[str] = Field(default=None)
            age: Optional[int] = Field(default=None)

        for form_schema_cls in (WithValid, WithValidField):
            form = Form[BaseModel](
                id="myform",
                workflow_run_id="myworkflowrun",
                workflow_id="myworkflow",
                form_schema=form_schema_cls,
            )
            assert form.id == "myform"
            assert form.workflow_run_id == "myworkflowrun"
            assert form.form_schema == form_schema_cls

    def test_form_serialization(self) -> None:
        form = Form[TicketOrderForm](
            id="myform",
            workflow_run_id="myworkflowrun",
            workflow_id="myworkflow",
            path="/task/step",
            form_schema=TicketOrderForm,
            metadata={"organization": "fixpoint.co"},
        )
        form.update_contents(TicketOrderForm(name="Dylan", age=32))
        serialized = form.serialize()

        # It can be serialized to text/json
        json_serialized = json.dumps(serialized)
        serialized = json.loads(json_serialized)

        # deseriailization doesn't actually have access to the underlying Form
        # schema class because we dynamically create a new Pydantic model when
        # deserializing.
        des_form: Form[BaseModel] = Form.deserialize(serialized)
        # But you can cast the type if you want and if you know what your form's type is!
        new_form = cast(Form[TicketOrderForm], des_form)

        assert new_form.id == "myform"
        assert new_form.id == form.id

        assert new_form.workflow_run_id == "myworkflowrun"
        assert new_form.workflow_run_id == form.workflow_run_id

        assert new_form.path == "/task/step"
        assert new_form.path == form.path

        assert new_form.metadata == {"organization": "fixpoint.co"}
        assert new_form.metadata == form.metadata

        # We can't compare the contents directly, because when we deserialized
        # the saved form, we dynamically created a new Pydantic model class,
        # which is different than the prior Pydantic model class.
        assert form.contents.model_dump() == new_form.contents.model_dump()
        assert new_form.contents.model_dump() == {
            "name": "Dylan",
            "age": 32,
            "email": None,
            "ticket_cost": None,
        }

        # Because we properly serialized and deserialized the form schema, it
        # should complain when we try to set a field incorrectly.
        with pytest.raises(Exception):
            new_form.update_contents({"bad": "contents"})

        with pytest.raises(Exception):
            new_form.update_contents({"age": "I am older than time itself"})

        new_form.update_contents({"age": 100})
        assert new_form.contents.age == 100

    def test_form_serialization_no_contents(self) -> None:
        # TODO(dbmikus) fix this test and don't skip it
        pytest.skip("skip it")

        form = Form[TicketOrderForm](
            id="myform",
            workflow_run_id="myworkflowrun",
            path="/task/step",
            form_schema=TicketOrderForm,
        )
        serialized = form.serialize()
        assert serialized["contents"] == {"age": None, "email": None, "name": None}
        new_form: Form[TicketOrderForm] = Form.deserialize(serialized)
        assert new_form.contents == TicketOrderForm()

    def test_form_update_contents_dict(self) -> None:
        self.assert_form_update_contents(use_model=False)

    def test_form_update_contents_model(self) -> None:
        self.assert_form_update_contents(use_model=True)

    def assert_form_update_contents(self, use_model: bool) -> None:

        if use_model:

            def contents_converter(
                contents: Dict[str, Any]
            ) -> Union[TicketOrderForm, Dict[str, Any]]:
                return TicketOrderForm(**contents)

        else:

            def contents_converter(
                contents: Dict[str, Any]
            ) -> Union[TicketOrderForm, Dict[str, Any]]:
                return contents

        form = Form[TicketOrderForm](
            id="myform",
            workflow_run_id="myworkflowrun",
            workflow_id="myworkflow",
            path="/task/step",
            form_schema=TicketOrderForm,
        )
        assert form.contents == TicketOrderForm()

        # only do this if we are parsing the contents as a dict, because if
        # contents_converter converts to a Pydantic model it will strip out the
        # bad contents according to `model_config['extra']`
        if not use_model:
            with pytest.raises(Exception):
                form.update_contents(contents_converter({"bad": "contents"}))

        assert form.contents == TicketOrderForm()

        form.update_contents(contents_converter({"name": "Dylan", "age": 32}))
        assert form.contents == TicketOrderForm(name="Dylan", age=32)

        with pytest.raises(Exception):
            form.update_contents(contents_converter({"age": "My age is 9000"}))
        assert form.contents == TicketOrderForm(name="Dylan", age=32)

        form.update_contents(contents_converter({"email": "hello@fixpoint.co"}))
        assert form.contents == TicketOrderForm(
            name="Dylan", age=32, email="hello@fixpoint.co"
        )

        form.update_contents(contents_converter({"name": "Jakub"}))
        assert form.contents == TicketOrderForm(
            name="Jakub", age=32, email="hello@fixpoint.co"
        )

        form.update_contents(contents_converter({"name": None}))
        assert form.contents == TicketOrderForm(
            name=None, age=32, email="hello@fixpoint.co"
        )

    def test_workflow_forms(self) -> None:
        workflow = Workflow(
            id="test_workflow",
        )
        assert workflow.id == "test_workflow"
        self.assert_workflow_forms_works(workflow)

    @pytest.mark.skipif(
        not is_supabase_enabled(),
        reason="Disabled until we have a supabase instance running in CI",
    )
    @pytest.mark.parametrize(
        "supabase_setup_url_and_key",
        [
            (
                f"""
        CREATE TABLE IF NOT EXISTS public.forms_with_metadata (
            id text PRIMARY KEY,
            workflow_id text,
            workflow_run_id text,
            metadata jsonb,
            path text NOT NULL,
            contents jsonb NOT NULL,
            form_schema text NOT NULL,
            versions jsonb,
            task text,
            step text
        );

        TRUNCATE TABLE public.forms_with_metadata
        """,
                "public.forms_with_metadata",
            )
        ],
        indirect=True,
    )
    def test_workflow_forms_with_storage(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key

        form_storage = create_form_supabase_storage(url, key)

        workflow = Workflow(
            id="test_workflow",
            form_storage=form_storage,
        )
        self.assert_workflow_forms_works(workflow)

    def assert_workflow_forms_works(self, workflow: Workflow) -> None:
        assert workflow.id == "test_workflow"

        run = workflow.run()
        assert run.id is not None

        # Store the form on the run
        stored_form = run.forms.store(
            form_id="foo",
            schema=TicketOrderForm,
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

        # Updating form with invalid contents should fail
        with pytest.raises(Exception):
            run.forms.update(form_id="foo", contents={"bad": "contents"})

        # Updated form
        updated_form: Form[TicketOrderForm] = run.forms.update(
            form_id="foo",
            contents={"name": "Dylan"},
            metadata={"mymeta": "data is here!"},
        )
        assert isinstance(updated_form, Form)
        assert updated_form.id == "foo"
        # path is not updated
        assert updated_form.path == "/foo"
        assert updated_form.contents.model_dump() == {
            "name": "Dylan",
            "age": None,
            "email": None,
            "ticket_cost": None,
        }
        assert updated_form.metadata == {"mymeta": "data is here!"}

        # Updating the form contents preserves old contents, merging in the update
        updated_form = run.forms.update(
            form_id="foo", contents={"email": "hello@fixpoint.co"}
        )
        assert updated_form.contents.model_dump() == {
            "name": "Dylan",
            "age": None,
            "email": "hello@fixpoint.co",
            "ticket_cost": None,
        }

        # List forms
        listed_forms = run.forms.list()

        assert isinstance(listed_forms, List)
        assert len(listed_forms) == 1
        assert isinstance(listed_forms[0], Form)
        assert listed_forms[0].id == "foo"
        assert listed_forms[0].path == "/foo"
        assert listed_forms[0].metadata == {"mymeta": "data is here!"}


class TestFormTypeHelpers:
    def test_is_valid_field_annotation(self) -> None:
        assert not _is_valid_field_annotation(None)
        assert not _is_valid_field_annotation(int)
        assert not _is_valid_field_annotation(Union[int, str])
        assert not _is_valid_field_annotation(Optional[list])
        assert not _is_valid_field_annotation(Optional[dict])
        assert not _is_valid_field_annotation(Union[dict, int, None])

        assert _is_valid_field_annotation(Optional[int])
        assert _is_valid_field_annotation(Optional[float])
        assert _is_valid_field_annotation(Optional[str])
        assert _is_valid_field_annotation(Optional[bool])
        assert _is_valid_field_annotation(Union[int, None])
        assert _is_valid_field_annotation(Union[int, str, None])
        assert _is_valid_field_annotation(Optional[Union[int, bool, None]])
        assert _is_valid_field_annotation(Optional[Union[int, bool, str, float]])

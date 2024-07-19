import pathlib
from typing import Optional, Tuple, TypeVar

from pydantic import BaseModel, Field
import pytest

from fixpoint.workflows import imperative
from fixpoint.workflows.imperative import Form
from ...supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


T1 = TypeVar("T1", bound=BaseModel)
T2 = TypeVar("T2", bound=BaseModel)


class TestWorkflowRun:
    def test_clone(self) -> None:
        workflow = imperative.Workflow(id="test_workflow")
        run = workflow.run()
        new_run = run.clone()

        # should have same docs and forms
        assert new_run.docs is run.docs
        assert new_run.forms is run.forms

        # should have same storage_config
        assert new_run.storage_config is run.storage_config

        # id should be equal
        assert new_run.id == run.id

        # should have a new node_state
        # references are different...
        assert new_run._node_state is not run._node_state
        # but content is the same
        assert new_run.current_node_info.id == run.current_node_info.id

        # It's fine that workflow is the same, because we do not expect to
        # mutate it.
        assert new_run.workflow is run.workflow

    def test_on_disk_doc_storage(self, tmp_path: pathlib.Path) -> None:
        storage_config = imperative.StorageConfig.with_disk(
            storage_path=tmp_path.as_posix(),
            agent_cache_ttl_s=60,
        )
        self.assert_doc_storage(storage_config)

    @pytest.mark.skipif(
        not is_supabase_enabled(),
        reason="Supabase must be turned on",
    )
    @pytest.mark.parametrize(
        "supabase_setup_url_and_key",
        [
            (
                f"""
        CREATE TABLE IF NOT EXISTS public.documents (
            id text PRIMARY KEY,
            workflow_id text,
            workflow_run_id text,
            path text NOT NULL,
            metadata jsonb NOT NULL,
            contents text NOT NULL,
            task text,
            step text,
            versions jsonb
        );

        TRUNCATE TABLE public.documents;
        """,
                "public.documents",
            )
        ],
        indirect=True,
    )
    def test_supabase_doc_storage(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key
        storage_config = imperative.StorageConfig.with_supabase(
            supabase_url=url,
            supabase_api_key=key,
        )
        self.assert_doc_storage(storage_config)

    def assert_doc_storage(self, storage_config: imperative.StorageConfig) -> None:
        workflow = imperative.Workflow(id="test_workflow")
        run = workflow.run(storage_config=storage_config)
        doc = run.docs.store(
            id="test_doc",
            contents="test_contents",
            metadata={"author": "Dylan"},
            path="task1/step2",
        )
        assert doc.workflow_id == workflow.id
        assert doc.workflow_run_id == run.id
        fetched_doc = run.docs.get(document_id="test_doc")
        assert fetched_doc is not None
        assert fetched_doc == doc

        updated_doc = run.docs.update(
            document_id="test_doc",
            contents="updated_contents",
            metadata={"author": "Jakub"},
        )

        assert doc.id == updated_doc.id
        assert doc.path == updated_doc.path
        assert doc.workflow_id == updated_doc.workflow_id
        assert doc.workflow_run_id == updated_doc.workflow_run_id
        assert doc.contents != updated_doc.contents
        assert doc.metadata != updated_doc.metadata
        assert updated_doc.contents == "updated_contents"
        assert updated_doc.metadata == {"author": "Jakub"}

        doc2 = run.docs.store(
            id="doc2",
            contents="doc 2 contents",
        )
        fetched_doc2 = run.docs.get(document_id="doc2")
        assert fetched_doc2 is not None
        assert fetched_doc2 == doc2

        assert run.docs.get(document_id="test_doc") == updated_doc

        all_docs = run.docs.list()
        assert len(all_docs) == 2
        assert updated_doc in all_docs
        assert doc2 in all_docs

        step2_docs = run.docs.list(path="task1/step2")
        assert len(step2_docs) == 1
        assert updated_doc in step2_docs
        assert doc2 not in step2_docs

    def test_on_disk_form_storage(self, tmp_path: pathlib.Path) -> None:
        storage_config = imperative.StorageConfig.with_disk(
            storage_path=tmp_path.as_posix(),
            agent_cache_ttl_s=60,
        )
        self.assert_form_storage(storage_config)

    @pytest.mark.skipif(
        not is_supabase_enabled(),
        reason="Supabase must be turned on",
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

        TRUNCATE TABLE public.forms_with_metadata;
        """,
                "public.forms_with_metadata",
            )
        ],
        indirect=True,
    )
    def test_supabase_form_storage(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key
        storage_config = imperative.StorageConfig.with_supabase(
            supabase_url=url,
            supabase_api_key=key,
        )
        self.assert_form_storage(storage_config)

    def assert_form_storage(self, storage_config: imperative.StorageConfig) -> None:
        class Person(BaseModel):
            name: Optional[str] = Field(
                description="The name of the person", default=None
            )
            age: Optional[int] = Field(
                description="The age of the person", default=None
            )

        workflow = imperative.Workflow(id="test_workflow")
        run = workflow.run(storage_config=storage_config)
        form = run.forms.store(
            schema=Person,
            form_id="test_form",
            path="task1/step2",
            metadata={"author": "Dylan"},
        )

        assert form.workflow_id == workflow.id
        assert form.workflow_run_id == run.id
        assert form.path == "task1/step2"
        assert form.metadata == {"author": "Dylan"}
        assert form.form_schema == Person

        fetched_form = run.forms.get(form_id="test_form")
        assert fetched_form is not None
        # compare every field in form and fetched_form except "form_schema"
        for attr_key in form.model_fields:
            if attr_key != "form_schema":
                assert getattr(form, attr_key) == getattr(fetched_form, attr_key)
        assert (
            fetched_form.form_schema.model_json_schema()
            == form.form_schema.model_json_schema()
        )

        updated_form = run.forms.update(
            form_id="test_form",
            contents=Person(name="Jakub"),
            metadata={"classified_level": "super-secret"},
        )
        assert updated_form.id == form.id
        assert updated_form.workflow_id == workflow.id
        assert updated_form.workflow_run_id == run.id
        assert updated_form.path == "task1/step2"
        assert (
            updated_form.form_schema.model_json_schema() == Person.model_json_schema()
        )
        assert updated_form.contents.model_dump() == Person(name="Jakub").model_dump()
        assert updated_form.metadata == {"classified_level": "super-secret"}

        class PersonGoal(BaseModel):
            name: Optional[str] = Field(
                description="The name of the person", default=None
            )
            goal_description: Optional[str] = Field(
                description="The goal of the person", default=None
            )

        form_2 = run.forms.store(
            schema=PersonGoal,
            form_id="test_form_goal",
            path="task1/step3",
            metadata={"author": "Dylan"},
        )
        self.assert_compare_forms(form_2, run.forms.get(form_id="test_form_goal"))
        self.assert_compare_forms(updated_form, run.forms.get(form_id="test_form"))

        all_forms = run.forms.list()
        assert len(all_forms) == 2
        assert any(self.eq_forms(f, form_2) for f in all_forms)
        assert any(self.eq_forms(f, updated_form) for f in all_forms)

        step2_forms = run.forms.list(path="task1/step2")
        assert len(step2_forms) == 1
        assert not any(self.eq_forms(f, form_2) for f in step2_forms)
        assert any(self.eq_forms(f, updated_form) for f in step2_forms)

    def assert_compare_forms(
        self, form1: Form[T1] | None, form2: Form[T2] | None
    ) -> None:
        if form1 is None or form2 is None:
            assert form1 is None and form2 is None
            return

        # compare every field in form and fetched_form except "form_schema"
        for attr_key in form1.model_fields:
            if attr_key != "form_schema":
                assert getattr(form1, attr_key) == getattr(form2, attr_key)
        assert (
            form1.form_schema.model_json_schema()
            == form2.form_schema.model_json_schema()
        )

    def eq_forms(self, form1: Form[T1] | None, form2: Form[T2] | None) -> bool:
        if form1 is None or form2 is None:
            return form1 is None and form2 is None

        # compare every field in form and fetched_form except "form_schema"
        for attr_key in form1.model_fields:
            if attr_key != "form_schema":
                if not getattr(form1, attr_key) == getattr(form2, attr_key):
                    return False
        return (
            form1.form_schema.model_json_schema()
            == form2.form_schema.model_json_schema()
        )

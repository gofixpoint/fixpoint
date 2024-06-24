from typing import List, Tuple
import pytest
from fixpoint_extras.workflows.imperative.workflow import Workflow
from fixpoint_extras.workflows.imperative.document import Document
from fixpoint_extras.workflows.imperative.config import create_docs_supabase_storage

from tests.supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


class TestDocuments:

    def test_workflow_documents(self) -> None:
        workflow = Workflow(
            id="test_workflow",
        )
        assert workflow.id == "test_workflow"

        run = workflow.run()
        assert run.id is not None

        # Store the doc on the run
        stored_doc = run.documents.store(
            id="foo",
            contents="This is a test document",
            path="/foo",
            metadata={"foo": "bar"},
        )
        assert isinstance(stored_doc, Document)
        assert stored_doc.id == "foo"
        assert stored_doc.path == "/foo"
        assert stored_doc.metadata == {"foo": "bar"}
        assert stored_doc.contents == "This is a test document"

        # Retrieved doc from run with id
        retrieved_doc = run.documents.get(document_id="foo")
        assert isinstance(retrieved_doc, Document)
        assert retrieved_doc.id == "foo"
        assert retrieved_doc.path == "/foo"
        assert retrieved_doc.contents == "This is a test document"
        assert retrieved_doc.metadata == {"foo": "bar"}

        # Updated doc
        updated_doc: Document = run.documents.update(
            document_id="foo",
            contents="Updated contents",
            metadata={"mymeta": "data is here!"},
        )
        assert isinstance(updated_doc, Document)
        assert updated_doc.id == "foo"
        # path is not updated
        assert updated_doc.path == "/foo"
        assert updated_doc.contents == "Updated contents"
        assert updated_doc.metadata == {"mymeta": "data is here!"}

        # List docs
        listed_docs = run.documents.list()
        assert isinstance(listed_docs, List)
        assert len(listed_docs) == 1
        assert isinstance(listed_docs[0], Document)
        assert listed_docs[0].id == "foo"
        assert listed_docs[0].path == "/foo"
        assert listed_docs[0].contents == "Updated contents"
        assert listed_docs[0].metadata == {"mymeta": "data is here!"}

    @pytest.mark.skipif(
        not is_supabase_enabled(),
        reason="Disabled until we have a supabase instance running in CI",
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
            contents text NOT NULL
        );

        TRUNCATE TABLE public.documents
        """,
                "public.documents",
            )
        ],
        indirect=True,
    )
    def test_workflow_forms_with_storage(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key
        document_storage = create_docs_supabase_storage(url, key)

        workflow = Workflow(
            id="test_workflow",
            form_storage=document_storage,
        )
        assert workflow.id == "test_workflow"

        run = workflow.run()
        assert run.id is not None

        # Store the doc on the run
        stored_doc = run.documents.store(
            id="foo",
            contents="This is a test document",
            path="/foo",
            metadata={"foo": "bar"},
        )
        assert isinstance(stored_doc, Document)
        assert stored_doc.id == "foo"
        assert stored_doc.path == "/foo"
        assert stored_doc.metadata == {"foo": "bar"}
        assert stored_doc.contents == "This is a test document"

        # Retrieved doc from run with id
        retrieved_doc = run.documents.get(document_id="foo")
        assert isinstance(retrieved_doc, Document)
        assert retrieved_doc.id == "foo"
        assert retrieved_doc.path == "/foo"
        assert retrieved_doc.contents == "This is a test document"
        assert retrieved_doc.metadata == {"foo": "bar"}

        # Updated doc
        updated_doc: Document = run.documents.update(
            document_id="foo",
            contents="Updated contents",
            metadata={"mymeta": "data is here!"},
        )
        assert isinstance(updated_doc, Document)
        assert updated_doc.id == "foo"
        # path is not updated
        assert updated_doc.path == "/foo"
        assert updated_doc.contents == "Updated contents"
        assert updated_doc.metadata == {"mymeta": "data is here!"}

        # List docs
        listed_docs = run.documents.list()
        assert isinstance(listed_docs, List)
        assert len(listed_docs) == 1
        assert isinstance(listed_docs[0], Document)
        assert listed_docs[0].id == "foo"
        assert listed_docs[0].path == "/foo"
        assert listed_docs[0].contents == "Updated contents"
        assert listed_docs[0].metadata == {"mymeta": "data is here!"}

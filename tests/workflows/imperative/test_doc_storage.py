import pathlib
from typing import List, Optional, Tuple

import pytest

from fixpoint._storage import definitions as storage_definitions
from fixpoint.workflows.imperative.workflow import Workflow
from fixpoint.workflows.imperative._doc_storage import (
    DocStorage,
    SupabaseDocStorage,
    OnDiskDocStorage,
)
from fixpoint.workflows.imperative.document import Document
from fixpoint.workflows.imperative.config import create_docs_supabase_storage
from fixpoint.utils.storage import new_sqlite_conn

from tests.supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


@pytest.mark.skipif(
    not is_supabase_enabled(),
    reason="Disabled until we have a supabase instance running in CI",
)
@pytest.mark.parametrize(
    "supabase_setup_url_and_key",
    [
        (
            f"""
    {storage_definitions.DOCS_POSTGRES_TABLE}

    TRUNCATE TABLE public.documents;
    """,
            "public.documents",
        )
    ],
    indirect=True,
)
def test_postgres_docs_primary_keys(
    supabase_setup_url_and_key: Tuple[str, str]
) -> None:
    supabase_url, supabase_key = supabase_setup_url_and_key
    storage = create_docs_supabase_storage(supabase_url, supabase_key)
    assert_docs_primary_keys(storage)


def test_ondisk_docs_primary_keys() -> None:
    storage = OnDiskDocStorage(new_sqlite_conn(":memory:"))
    assert_docs_primary_keys(storage)


def assert_docs_primary_keys(doc_storage: DocStorage) -> None:
    # within a given workflow and a workflow run, you can only use an ID once
    doc1 = _create_doc(
        id="doc1",
        workflow_id="workflow1",
        workflow_run_id="run1",
    )
    doc_storage.create(doc1)
    # trying it again fails
    with pytest.raises(Exception):
        doc_storage.create(doc1)

    # If you change the workflow run, you can use the ID again.
    # You can also set the run to None.
    for run_id in ("run2", None):
        doc2 = _create_doc(
            id="doc1",
            workflow_id="workflow1",
            workflow_run_id=run_id,
        )
        doc_storage.create(doc2)
        with pytest.raises(Exception):
            doc_storage.create(doc2)

    # If you change the workflow, you can use the ID again.
    # You can also set the workflow to None.
    for w_id in ("workflow2", None):
        doc3 = _create_doc(
            id="doc1",
            workflow_id=w_id,
            workflow_run_id="run1",
        )
        doc_storage.create(doc3)
        with pytest.raises(Exception):
            doc_storage.create(doc3)

    ####
    # now lets try to get the rows and make sure everything is working
    ####
    _assert_fetch(doc_storage, "doc1", "workflow1", "run1")
    _assert_fetch(doc_storage, "doc1", "workflow1", "run2")
    _assert_fetch(doc_storage, "doc1", "workflow1", None)
    _assert_fetch(doc_storage, "doc1", "workflow2", "run1")
    _assert_fetch(doc_storage, "doc1", None, "run1")

    ####
    # try the updates
    ####
    update_test_defs = [
        ("doc1", "workflow1", "run1"),
        ("doc1", "workflow1", "run2"),
        ("doc1", "workflow1", None),
        ("doc1", "workflow2", "run1"),
        ("doc1", None, "run1"),
    ]
    for id, wid, wrid in update_test_defs:
        doc_content = _create_doc(id, wid, wrid).contents
        doc_updated_content = doc_content + ".updated"
        new_doc = _create_doc(id, wid, wrid)
        new_doc.contents = doc_updated_content

        other_old_docs = _build_other_docs_list(
            doc_storage,
            update_test_defs,
            id,
            wid,
            wrid,
        )

        doc_storage.update(new_doc)
        new_fetched_doc = doc_storage.get(id=id, workflow_id=wid, workflow_run_id=wrid)
        assert new_doc == new_fetched_doc
        assert new_fetched_doc.contents == doc_updated_content

        # make sure none of the other docs were updated
        other_new_docs = _build_other_docs_list(
            doc_storage,
            update_test_defs,
            id,
            wid,
            wrid,
        )
        assert other_old_docs == other_new_docs
        for other_doc in other_new_docs:
            assert other_doc.contents != new_fetched_doc.contents

    ####
    # try listing
    ####
    all_list = list_sorted(doc_storage)
    assert all_list == [
        _create_doc("doc1", None, "run1", updated=True),
        _create_doc("doc1", "workflow1", None, updated=True),
        _create_doc("doc1", "workflow1", "run1", updated=True),
        _create_doc("doc1", "workflow1", "run2", updated=True),
        _create_doc("doc1", "workflow2", "run1", updated=True),
    ]

    wf1_list = list_sorted(doc_storage, "workflow1")
    assert wf1_list == [
        _create_doc("doc1", "workflow1", None, updated=True),
        _create_doc("doc1", "workflow1", "run1", updated=True),
        _create_doc("doc1", "workflow1", "run2", updated=True),
    ]

    wf2_list = list_sorted(doc_storage, "workflow2")
    assert wf2_list == [_create_doc("doc1", "workflow2", "run1", updated=True)]

    run1_list = list_sorted(doc_storage, workflow_run_id="run1")
    assert run1_list == [
        _create_doc("doc1", None, "run1", updated=True),
        _create_doc("doc1", "workflow1", "run1", updated=True),
        _create_doc("doc1", "workflow2", "run1", updated=True),
    ]

    wf1_run1_list = list_sorted(doc_storage, "workflow1", "run1")
    assert wf1_run1_list == [
        _create_doc("doc1", "workflow1", "run1", updated=True),
    ]

    run2_list = list_sorted(doc_storage, workflow_run_id="run2")
    assert run2_list == [
        _create_doc("doc1", "workflow1", "run2", updated=True),
    ]


def list_sorted(
    doc_storage: DocStorage,
    workflow_id: Optional[str] = None,
    workflow_run_id: Optional[str] = None,
) -> List[Document]:
    return sorted(
        doc_storage.list(workflow_id=workflow_id, workflow_run_id=workflow_run_id),
        key=lambda d: (
            d.id,
            d.workflow_id or "__null__",
            d.workflow_run_id or "__null__",
        ),
    )


def _build_other_docs_list(
    doc_storage: DocStorage,
    test_defs: List[Tuple[str, Optional[str], Optional[str]]],
    id: str,
    wid: Optional[str],
    wrid: Optional[str],
) -> List[Document]:
    other_docs: List[Document] = []
    for idother, widother, wridother in test_defs:
        if (idother, widother, wridother) != (id, wid, wrid):
            doc = doc_storage.get(
                id=idother, workflow_id=widother, workflow_run_id=wridother
            )
            assert doc is not None
            other_docs.append(doc)
    return other_docs


def _assert_fetch(
    doc_storage: DocStorage,
    id: str,
    workflow_id: Optional[str],
    workflow_run_id: Optional[str],
) -> None:
    fetched_doc = doc_storage.get(
        id=id, workflow_id=workflow_id, workflow_run_id=workflow_run_id
    )
    assert fetched_doc == _create_doc(
        id=id, workflow_id=workflow_id, workflow_run_id=workflow_run_id
    )


def _create_doc(
    id: str,
    workflow_id: Optional[str],
    workflow_run_id: Optional[str],
    updated: bool = False,
) -> Document:
    contents = (
        f'{workflow_id or "__null__"}.{workflow_run_id or "__null__"}.{id}.contents'
    )
    if updated:
        contents += ".updated"
    return Document(
        id=id,
        workflow_id=workflow_id,
        workflow_run_id=workflow_run_id,
        contents=contents,
    )

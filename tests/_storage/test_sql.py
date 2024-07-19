from fixpoint._storage.sql import format_where_clause


def test_format_where_clause() -> None:
    d = {
        "path": "task/step",
        "workflow_run_id": "abc-123",
    }
    assert (
        format_where_clause(d)
        == "WHERE path = :path AND workflow_run_id = :workflow_run_id"
    )

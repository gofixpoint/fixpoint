from typing import Generator, Tuple, Any
import psycopg
import pytest
from .storage.postgres_helper import drop_table

from fixpoint.utils.env import get_env_value


@pytest.fixture
def test_inputs(
    request: pytest.FixtureRequest,
) -> Generator[Tuple[str, str], None, None]:
    setup_sql_command, table = request.param
    url = get_env_value("SUPABASE_URL")
    key: str = get_env_value("SUPABASE_KEY")
    pg_url = get_env_value("POSTGRES_URL")

    _setup_test_tables(pg_url, setup_sql_command)
    yield url, key
    _teardown_test_tables(pg_url, table)


def _setup_test_tables(pg_url: str, setup_sql_command: str) -> None:
    try:
        conn = psycopg.connect(
            conninfo=pg_url,
        )

        cur = conn.cursor()
        cur.execute(setup_sql_command)

        conn.commit()
    except Exception as e:
        print(f"Error creating test table: {e}")
        conn.close()
        raise e
    finally:
        cur.close()
        conn.close()


def _teardown_test_tables(pg_url: str, table: str) -> None:
    try:
        conn = psycopg.connect(
            conninfo=pg_url,
        )
        drop_table(conn, table)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        conn.close()

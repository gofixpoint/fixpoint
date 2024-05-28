from typing import Generator, Tuple
import pytest
import psycopg
from pydantic import BaseModel
from fixpoint.storage import SupabaseStorage
from fixpoint.utils.db.postgres import drop_table
from fixpoint.utils.env import get_env_value


@pytest.mark.skip(reason="Disabled until we have a supabase instance running in CI")
class TestSupabaseStorage:

    @staticmethod
    @pytest.fixture
    def test_inputs() -> Generator[Tuple[str, str], None, None]:
        url = get_env_value("SUPABASE_URL")
        key: str = get_env_value("SUPABASE_KEY")
        pg_url = get_env_value("POSTGRES_URL")

        TestSupabaseStorage._setup_test_tables(pg_url)
        yield url, key
        # TestSupabaseStorage._teardown_test_tables(pg_url)

    @staticmethod
    def _setup_test_tables(pg_url: str) -> None:
        try:
            conn = psycopg.connect(
                conninfo=pg_url,
            )

            cur = conn.cursor()

            sql_command = """
            CREATE TABLE IF NOT EXISTS public.person_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150),
                age INT
            );

            TRUNCATE TABLE public.person_table
            """
            cur.execute(sql_command)

            conn.commit()
        except Exception as e:
            print(f"Error creating test table: {e}")
            conn.close()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def _teardown_test_tables(pg_url: str) -> None:
        try:
            conn = psycopg.connect(
                conninfo=pg_url,
            )
            drop_table(conn, "public.person_table")
        except Exception as e:
            print("An error occurred:", e)
        finally:
            conn.close()

    def test_client_instantiation(self, test_inputs: Tuple[str, str]) -> None:
        url, key = test_inputs
        store = SupabaseStorage(url, key)

        class Person(BaseModel):
            id: int
            name: str
            age: int

        # Test that inserts work
        responses = store.insert(
            resource="person_table",
            data=[{"name": "John", "age": 30}, {"name": "Elizabeth", "age": 35}],
            model=Person,
        )

        # Check that we got the right amount and types of responses
        assert len(responses) == 2
        assert isinstance(responses, list)
        assert isinstance(responses[0], Person)
        assert responses[0].name == "John"
        assert responses[0].age == 30
        assert isinstance(responses[1], Person)
        assert responses[1].name == "Elizabeth"
        assert responses[1].age == 35

        # Fetching latest should return Elizabeth
        result = store.fetch_latest(
            resource="person_table",
            n=1,
            order_key="id",
            model=Person,
        )

        assert len(result) == 1
        assert result[0].name == "Elizabeth"
        assert result[0].age == 35

        # Fetching by id should return John
        results = store.fetch(
            resource="person_table",
            filter_criteria={"id": 1},
            model=Person,
        )
        assert len(results) == 1
        assert results[0].name == "John"
        assert results[0].age == 30

        # Update should update the age of John to 31
        resp = store.update(
            resource="person_table",
            data={"id": 1, "name": "John", "age": 31},
        )

        # Fetching without a model should return a list of dicts
        results = store.fetch(
            resource="person_table",
            filter_criteria={"id": 1},
        )
        assert len(results) == 1
        assert results[0]["name"] == "John"
        assert results[0]["age"] == 31

        # Delete should remove Elizabeth
        store.delete(
            resource="person_table",
            filter_criteria={"id": 2},
        )
        result = store.fetch(
            resource="person_table",
            filter_criteria={"id": 2},
        )
        assert result == []

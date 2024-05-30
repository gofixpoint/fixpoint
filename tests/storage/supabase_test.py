from typing import Generator, Tuple, Any
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
        TestSupabaseStorage._teardown_test_tables(pg_url)

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

        class Person(BaseModel):
            id: int
            name: str
            age: int

            def to_dict(self) -> dict[str, Any]:
                return self.__dict__

        store = SupabaseStorage[Person](
            url,
            key,
            table="person_table",
            order_key="id",
            id_column="id",
            value_type=Person,
        )

        john = Person(id=1, name="John", age=30)
        elizabeth = Person(id=2, name="Elizabeth", age=35)

        # Test that inserts work
        response = store.insert(data=john)
        assert isinstance(response, Person)
        assert response.name == "John"
        assert response.age == 30

        response = store.insert(data=elizabeth)
        assert isinstance(response, Person)
        assert response.name == "Elizabeth"
        assert response.age == 35

        # Fetching latest should return Elizabeth
        result = store.fetch_latest(n=1)

        assert len(result) == 1
        assert result[0].name == "Elizabeth"
        assert result[0].age == 35

        # Fetching by id should return John
        john_result = store.fetch(1)
        assert isinstance(john_result, Person)
        assert john_result.name == "John"
        assert john_result.age == 30

        # Update should update the age of John to 31
        older_john = Person(id=1, name="John", age=31)
        resp = store.update(data=older_john)
        assert isinstance(resp, Person)
        assert resp.name == "John"
        assert resp.age == 31

        older_john_result = store.fetch(resource_id=1)
        assert isinstance(older_john_result, Person)
        assert older_john_result.name == "John"
        assert older_john_result.age == 31

        # Delete should remove Elizabeth
        store.delete(resource_id=2)

        # assert that value error is raised
        with pytest.raises(RuntimeError):
            store.fetch(resource_id=2)

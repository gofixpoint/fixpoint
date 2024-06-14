from typing import Tuple, Any
import pytest
from pydantic import BaseModel
from fixpoint.storage import SupabaseStorage
from ..supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


@pytest.mark.skipif(
    not is_supabase_enabled(),
    reason="Disabled until we have a supabase instance running in CI",
)
class TestSupabaseStorage:

    @pytest.mark.parametrize(
        "supabase_setup_url_and_key",
        [
            (
                f"""
        CREATE TABLE IF NOT EXISTS public.person_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(150),
            age INT
        );

        TRUNCATE TABLE public.person_table
        """,
                "public.person_table",
            )
        ],
        indirect=True,
    )
    def test_client_instantiation(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key

        class Person(BaseModel):
            id: int
            name: str
            age: int

            def serialize(self) -> dict[str, Any]:
                """Method to get the serialized data of the item"""
                return self.__dict__

            @classmethod
            def deserialize(cls, data: dict[str, Any]) -> "Person":
                """Method to get the deserialized data of the item"""
                return Person(**data)

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
        assert store.fetch(resource_id=2) == None

from typing import List, Tuple
import pytest
from fixpoint.completions import ChatCompletionMessageParam
from fixpoint.memory import Memory, MemoryItem
from fixpoint.agents.mock import new_mock_completion
from fixpoint.storage.supabase import SupabaseStorage


class TestWithMemory:
    def test_store_memory(self) -> None:
        memstore = Memory()
        assert memstore.memory() == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl = new_mock_completion()
        memstore.store_memory(msgs, cmpl)
        assert memstore.memory() == [MemoryItem(messages=msgs, completion=cmpl)]

@pytest.mark.skip(reason="Disabled until we have a supabase instance running in CI")
class TestWithMemoryWithStorage:

    @pytest.mark.parametrize(
        "test_inputs",
        [
            (
                f"""
        CREATE TABLE IF NOT EXISTS public.memory_store (
            messages jsonb PRIMARY KEY,
            completion jsonb,
            workflow jsonb,
        );

        TRUNCATE TABLE public.memory_store;
        """,
                "public.memory_store",
            )
        ],
        indirect=True,
    )
    def test_store_memory_with_storage(self,  test_inputs: Tuple[str, str]) -> None:
        url, key = test_inputs
        storage = SupabaseStorage(
            url,
            key,
            table="memory_state",
            order_key="messages",
            id_column="messages",
            value_type=MemoryItem,
        )

        memstore = Memory(storage=storage)
        assert memstore.memory() == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl = new_mock_completion()
        memstore.store_memory(msgs, cmpl)
        assert memstore.memory() == [MemoryItem(messages=msgs, completion=cmpl)]


from typing import List, Tuple
import json
import pytest
from fixpoint.completions import ChatCompletionMessageParam
from fixpoint.memory import Memory, MemoryItem
from fixpoint.agents.mock import new_mock_completion
from fixpoint.storage.supabase import SupabaseStorage
from ..supabase_test_utils import test_inputs


class TestWithMemory:
    def test_store_memory(self) -> None:
        memstore = Memory()
        assert memstore.memory() == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl = new_mock_completion()
        memstore.store_memory(msgs, cmpl)

        stored_memory = memstore.memory()
        expected_memory = [MemoryItem(messages=msgs, completion=cmpl)]

        assert len(stored_memory) == len(expected_memory) == 1

        first_stored_memory = stored_memory[0]
        first_expected_memory = expected_memory[0]
        assert first_stored_memory.messages == first_expected_memory.messages
        assert first_stored_memory.completion == first_expected_memory.completion
        assert first_stored_memory.workflow == first_expected_memory.workflow


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
            workflow jsonb
        );

        TRUNCATE TABLE public.memory_store
        """,
                "public.memory_store",
            )
        ],
        indirect=True,
    )
    def test_store_memory_with_storage(self, test_inputs: Tuple[str, str]) -> None:
        url, key = test_inputs
        storage = SupabaseStorage(
            url,
            key,
            table="memory_store",
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

        stored_memory = memstore.memory()
        expected_memory = [MemoryItem(messages=msgs, completion=cmpl)]

        assert len(stored_memory) == len(expected_memory) == 1

        first_stored_memory = stored_memory[0]
        first_expected_memory = expected_memory[0]

        # The objects aren't the same address anymore, so we can't just compare them
        assert json.dumps(first_stored_memory.messages) == json.dumps(
            first_expected_memory.messages
        )
        assert (
            first_stored_memory.completion.serialize_json()
            == first_expected_memory.completion.serialize_json()
        )
        assert json.dumps(first_stored_memory.workflow) == json.dumps(
            first_expected_memory.workflow
        )

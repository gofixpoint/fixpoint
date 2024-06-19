import json
import pytest
from typing import List, Tuple

from pydantic import BaseModel

from fixpoint.completions import ChatCompletionMessageParam, ChatCompletion
from fixpoint.memory import Memory, MemoryItem
from fixpoint.agents.mock import new_mock_completion
from fixpoint.storage.supabase import SupabaseStorage
from ..supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


class TestWithMemory:
    def test_store_memory(self) -> None:
        memstore = Memory()
        assert memstore.memories() == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl: ChatCompletion[BaseModel] = new_mock_completion()
        memstore.store_memory(msgs, cmpl)

        stored_memory = memstore.memories()
        expected_memory = [MemoryItem(messages=msgs, completion=cmpl)]

        assert len(stored_memory) == len(expected_memory) == 1

        first_stored_memory = stored_memory[0]
        first_expected_memory = expected_memory[0]
        assert first_stored_memory.messages == first_expected_memory.messages
        assert first_stored_memory.completion == first_expected_memory.completion
        assert first_stored_memory.workflow_run == first_expected_memory.workflow_run


@pytest.mark.skipif(
    not is_supabase_enabled(),
    reason="Disabled until we have a supabase instance running in CI",
)
class TestWithMemoryWithStorage:

    @pytest.mark.parametrize(
        "supabase_setup_url_and_key",
        [
            (
                f"""
        CREATE TABLE IF NOT EXISTS public.memory_store (
            messages jsonb PRIMARY KEY,
            completion jsonb,
            workflow jsonb,
            workflow_run jsonb
        );

        TRUNCATE TABLE public.memory_store;
        """,
                "public.memory_store",
            )
        ],
        indirect=True,
    )
    def test_store_memory_with_storage(
        self, supabase_setup_url_and_key: Tuple[str, str]
    ) -> None:
        url, key = supabase_setup_url_and_key
        storage = SupabaseStorage(
            url,
            key,
            table="memory_store",
            order_key="messages",
            id_column="messages",
            value_type=MemoryItem,
        )

        memstore = Memory(storage=storage)
        assert memstore.memories() == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl: ChatCompletion[BaseModel] = new_mock_completion()
        memstore.store_memory(msgs, cmpl)

        stored_memory = memstore.memories()
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
        assert json.dumps(first_stored_memory.workflow_run) == json.dumps(
            first_expected_memory.workflow_run
        )

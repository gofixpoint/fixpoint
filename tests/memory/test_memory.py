import json
import pytest
from typing import List, Tuple

from pydantic import BaseModel

from fixpoint.completions import ChatCompletionMessageParam, ChatCompletion
from fixpoint.memory import Memory, MemoryItem, SupabaseMemory
from fixpoint.agents.mock import new_mock_completion
from ..supabase_test_utils import supabase_setup_url_and_key, is_supabase_enabled


class TestWithMemory:
    def test_store_memory(self) -> None:
        memstore = Memory()
        assert list(memstore.memories()) == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl: ChatCompletion[BaseModel] = new_mock_completion()
        memstore.store_memory("agent-1", msgs, cmpl)

        stored_memory = list(memstore.memories())
        expected_memory = [
            MemoryItem(agent_id="agent-1", messages=msgs, completion=cmpl)
        ]

        assert len(stored_memory) == len(expected_memory) == 1

        first_stored_memory = stored_memory[0]
        first_expected_memory = expected_memory[0]
        assert first_stored_memory.messages == first_expected_memory.messages
        assert first_stored_memory.completion == first_expected_memory.completion
        assert (
            first_stored_memory.workflow_run_id == first_expected_memory.workflow_run_id
        )
        assert first_stored_memory.workflow_id == first_expected_memory.workflow_id


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
            id text PRIMARY KEY,
            agent_id text NOT NULL,
            messages jsonb NOT NULL,
            completion jsonb,
            workflow_id text,
            workflow_run_id text,
            created_at timestamp with time zone DEFAULT now()
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
        memstore = SupabaseMemory(url, key)
        assert list(memstore.memories()) == []
        msgs: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": "hello!"}
        ]
        cmpl: ChatCompletion[BaseModel] = new_mock_completion()
        memstore.store_memory("agent-1", msgs, cmpl)

        stored_memory = list(memstore.memories())
        expected_memory = [
            MemoryItem(agent_id="agent-1", messages=msgs, completion=cmpl)
        ]

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
        assert first_stored_memory.workflow_id == first_expected_memory.workflow_id
        assert (
            first_stored_memory.workflow_run_id == first_expected_memory.workflow_run_id
        )

        fetched_mem = memstore.get(first_stored_memory.id)
        assert fetched_mem is not None
        assert fetched_mem.agent_id == first_stored_memory.agent_id
        assert fetched_mem.messages == first_stored_memory.messages
        assert fetched_mem.completion == first_stored_memory.completion
        assert fetched_mem.workflow_id == first_stored_memory.workflow_id
        assert fetched_mem.workflow_run_id == first_stored_memory.workflow_run_id

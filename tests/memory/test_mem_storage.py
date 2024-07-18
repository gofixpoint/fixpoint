import datetime
from typing import List, Optional

from fixpoint.completions import ChatCompletion
from fixpoint.agents.mock import new_mock_completion
from fixpoint.utils.messages import smsg, umsg
from fixpoint.utils.storage import new_sqlite_conn
from fixpoint.memory import MemoryItem
from fixpoint.memory._mem_storage import OnDiskMemoryStorage


class TestOnDiskMemoryStorage:
    def create_mem_item(
        self,
        *,
        created_at: Optional[datetime.datetime] = None,
        id: Optional[str] = None
    ) -> MemoryItem:
        mem_item = MemoryItem(
            agent_id="agent_1",
            workflow_id="workflow_1",
            workflow_run_id="run_1",
            messages=[smsg("You are a system message"), umsg("You are a user message")],
            completion=new_mock_completion(),
            created_at=created_at or datetime.datetime.now(),
            _id=id,
        )
        return mem_item

    def test_insert(self) -> None:
        """Test inserting a memory item"""
        storage = OnDiskMemoryStorage(new_sqlite_conn(":memory:"))
        mem_item = self.create_mem_item()
        storage.insert(mem_item)
        result = storage.get(mem_item.id)

        assert result is not None
        assert result == mem_item
        # also check the individual fields, in case the MemoryItem.__eq__ method is implemented wrong
        assert result.id == mem_item.id
        assert result.agent_id == mem_item.agent_id
        assert result.workflow_id == mem_item.workflow_id
        assert result.workflow_run_id == mem_item.workflow_run_id
        assert result.messages == mem_item.messages
        assert result.completion == mem_item.completion

    def test_get(self) -> None:
        """Test getting a memory item by ID"""
        mem_item = self.create_mem_item()
        storage = OnDiskMemoryStorage(new_sqlite_conn(":memory:"))
        storage.insert(mem_item)
        result = storage.get(mem_item.id)
        assert result is not None
        assert result.id == mem_item.id

        assert len(mem_item.id) > 0
        # make sure we create a different ID
        id_list = list(mem_item.id)
        if id_list[-1] == "f":
            id_list[-1] = "0"
        else:
            id_list[-1] = "f"

        result = storage.get("".join(id_list))
        assert result is None

    def test_list(self) -> None:
        """Test listing memory items"""
        storage = OnDiskMemoryStorage(new_sqlite_conn(":memory:"))

        mem_items: List[MemoryItem] = [
            # different times are sorted in descending order
            self.create_mem_item(id="id_1", created_at=self.new_datetime(5)),
            self.create_mem_item(id="id_3", created_at=self.new_datetime(2)),
            self.create_mem_item(id="id_2", created_at=self.new_datetime(3)),
            # if times are the same, the highest ID is returned
            self.create_mem_item(id="id_4", created_at=self.new_datetime(0)),
            self.create_mem_item(id="id_6", created_at=self.new_datetime(0)),
            self.create_mem_item(id="id_5", created_at=self.new_datetime(0)),
            self.create_mem_item(id="id_7", created_at=self.new_datetime(0)),
        ]

        for mem_item in mem_items:
            storage.insert(mem_item)

        response = storage.list(n=2)
        assert len(response.memories) == 2
        assert response.next_cursor is not None
        assert response.memories[0] == mem_items[0]
        assert response.memories[1] == mem_items[2]

        response = storage.list(cursor=response.next_cursor, n=2)
        assert len(response.memories) == 2
        assert response.memories[0] == mem_items[1]
        assert response.memories[1] == mem_items[3]
        assert response.next_cursor is not None

        response = storage.list(cursor=response.next_cursor, n=2)
        assert len(response.memories) == 2
        assert response.memories[0] == mem_items[5]
        assert response.memories[1] == mem_items[4]
        assert response.next_cursor is not None

        response = storage.list(cursor=response.next_cursor, n=2)
        assert len(response.memories) == 1
        assert response.memories[0] == mem_items[6]
        assert response.next_cursor is None

    def new_datetime(self, seconds_offset: int) -> datetime.datetime:
        return datetime.datetime(
            year=2024,
            month=10,
            day=23,
            hour=9,
            minute=10,
            second=10 + seconds_offset,
        )

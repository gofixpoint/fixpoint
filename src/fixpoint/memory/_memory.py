"""Code for agent memory"""

from typing import List, Protocol, Tuple


from ..completions import ChatCompletionMessageParam, ChatCompletion


class WithMemoryProto(Protocol):
    """A protocol for adding memory to an agent"""

    def memory(self) -> List[Tuple[List[ChatCompletionMessageParam], ChatCompletion]]:
        """Get the memory"""

    def store_memory(
        self, messages: List[ChatCompletionMessageParam], completion: ChatCompletion
    ) -> None:
        """Store the memory"""

    def format_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""


class WithMemory(WithMemoryProto):
    """A composable class to add memory to an agent"""

    _memory: List[Tuple[List[ChatCompletionMessageParam], ChatCompletion]]

    def __init__(self) -> None:
        self._memory = []

    def callback(
        self, messages: List[ChatCompletionMessageParam], completion: ChatCompletion
    ) -> None:
        """Handle completions with memory context"""
        self.store_memory(messages, completion)

    def store_memory(
        self, messages: List[ChatCompletionMessageParam], completion: ChatCompletion
    ) -> None:
        """Store the memory

        Args:
            messages (List[ChatCompletionMessageParam]): List of message parameters.
            completion (Optional[ChatCompletion]): The completion object, if any.
        """
        self._memory.append((messages, completion))

    def memory(self) -> List[Tuple[List[ChatCompletionMessageParam], ChatCompletion]]:
        """Get the memory"""
        return self._memory

    def format_str(self) -> str:
        """Return the formatted string of messages. Useful for printing/debugging"""
        delim = "============================================================"
        lines = []
        for mem in self.memory():
            lines.extend(self._format_single_mem(mem[0], mem[1]))
            lines.append(delim)
        return "\n".join(lines)

    def _format_single_mem(
        self, messages: List[ChatCompletionMessageParam], completion: ChatCompletion
    ) -> List[str]:
        """Return the formatted string of a single memory entry"""
        lines = [f'{m["role"]}: {m["content"]}' for m in messages]
        lines.append(f"assistant: {completion.choices[0].message.content}")
        return lines


# Check that we implement the protocol
def _check(_c: WithMemoryProto) -> None:
    pass


_check(WithMemory())

"""Extend the memory interfaces and classes with data analysis tools."""

from typing import Any, Dict, TypedDict, List, Union, Optional

try:
    import pandas as pd
except ImportError as e:
    raise ImportError(
        "To use the analyze modules, run "
        "`pip install fixpoint[analyze]`"
        " to install the extra dependencies."
    ) from e


from fixpoint.logging import logger
from fixpoint.completions import ChatCompletionMessageParam
from fixpoint.memory import Memory


class _DataDict(TypedDict):
    turn_id: List[int]
    role: List[str]
    content: List[Union[str, None]]
    structured_output: List[Optional[Dict[str, Any]]]

    # The first (and often the only) tool call name
    tool_call_name: List[Optional[str]]
    # The first (and often the only) tool call arguments
    tool_call_args: List[Optional[str]]
    # In case there are other tool calls, show all of the tool call info here
    all_tool_call_names: List[List[str]]
    all_tool_call_args: List[List[str]]

    workflow_name: List[Optional[str]]


class DataframeMemory(Memory):
    """A memory implementation that can integrate with dataframe"""

    def to_dataframe(self) -> pd.DataFrame:
        """Return the memory as a dataframe"""

        data: _DataDict = {
            "turn_id": [],
            "role": [],
            "content": [],
            "structured_output": [],
            "tool_call_name": [],
            "tool_call_args": [],
            "all_tool_call_names": [],
            "all_tool_call_args": [],
            "workflow_name": [],
        }
        for idx, memitem in enumerate(self.memories()):
            messages = memitem.messages
            completion = memitem.completion
            workflow_run_id = memitem.workflow_run_id
            for message in messages:
                data["turn_id"].append(idx)
                data["role"].append(message["role"])
                data["content"].append(self._format_content_parts(message))
                data["structured_output"].append(None)
                data["tool_call_name"].append(None)
                data["tool_call_args"].append(None)
                data["all_tool_call_names"].append([])
                data["all_tool_call_args"].append([])
                data["workflow_name"].append(workflow_run_id)

            data["turn_id"].append(idx)
            data["role"].append("assistant")
            data["content"].append(completion.choices[0].message.content)
            so = completion.fixp.structured_output
            data["structured_output"].append(so.dict() if so else None)

            tool_calls = completion.choices[0].message.tool_calls
            if tool_calls:
                data["tool_call_name"].append(tool_calls[0].function.name)
                data["tool_call_args"].append(tool_calls[0].function.arguments)
                data["all_tool_call_names"].append(
                    [tc.function.name for tc in tool_calls]
                )
                data["all_tool_call_args"].append(
                    [tc.function.arguments for tc in tool_calls]
                )
            else:
                data["tool_call_name"].append(None)
                data["tool_call_args"].append(None)
                data["all_tool_call_names"].append([])
                data["all_tool_call_args"].append([])

            data["workflow_name"].append(workflow_run_id)
        return pd.DataFrame(data)

    def _format_content_parts(
        self, message: ChatCompletionMessageParam
    ) -> Union[str, None]:
        c = message["content"]
        if isinstance(c, str) or c is None:
            return c

        ctextparts = []
        for cpart in c:
            if cpart["type"] == "text":
                ctextparts.append(cpart["text"])
            else:
                logger.warning("Unsupported content type: %s", cpart["type"])
        return "\n".join(ctextparts)

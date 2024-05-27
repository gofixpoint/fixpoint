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


from ..logging import logger
from ..completions import ChatCompletionMessageParam
from ..memory import Memory


class _DataDict(TypedDict):
    turn_id: List[int]
    role: List[str]
    content: List[Union[str, None]]
    structured_output: List[Optional[Dict[str, Any]]]
    workflow_id: List[Optional[str]]


class DataframeMemory(Memory):
    """A memory implementation that can integrate with dataframe"""

    def to_dataframe(self) -> pd.DataFrame:
        """Return the memory as a dataframe"""

        data: _DataDict = {
            "turn_id": [],
            "role": [],
            "content": [],
            "structured_output": [],
            "workflow_id": [],
        }
        for idx, memitem in enumerate(self.memory()):
            messages = memitem.messages
            completion = memitem.completion
            workflow_id = memitem.workflow.id if memitem.workflow else None
            for message in messages:
                data["turn_id"].append(idx)
                data["role"].append(message["role"])
                data["content"].append(self._format_content_parts(message))
                data["structured_output"].append(None)
                data["workflow_id"].append(workflow_id)
            data["turn_id"].append(idx)
            data["role"].append("assistant")
            data["content"].append(completion.choices[0].message.content)
            so = completion.fixp.structured_output
            data["structured_output"].append(so.dict() if so else None)
            data["workflow_id"].append(workflow_id)
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

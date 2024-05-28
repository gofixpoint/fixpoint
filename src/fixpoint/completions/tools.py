"""Tool-calling and tool-use definitions"""

from openai.types.chat.chat_completion_tool_choice_option_param import (
    ChatCompletionToolChoiceOptionParam,
)
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

__all__ = ["ChatCompletionToolChoiceOptionParam", "ChatCompletionToolParam"]

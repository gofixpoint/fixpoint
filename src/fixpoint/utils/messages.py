"""Helpers for working with chat completion messages"""

from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)


def amsg(content: str) -> ChatCompletionAssistantMessageParam:
    """Create an assistant message"""
    return {"role": "assistant", "content": content}


def smsg(content: str) -> ChatCompletionSystemMessageParam:
    """Create a system message"""
    return {"role": "system", "content": content}


def umsg(content: str) -> ChatCompletionUserMessageParam:
    """Create a user message"""
    return {"role": "user", "content": content}

"""
The oai module contains the OpenAI-compatible interfaces for AI agents. That is,
you can make request like:

```
agent.chat.completions.create(...)
```
"""

from .openai import OpenAI

__all__ = ["OpenAI"]

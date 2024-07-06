"""
Wraps OpenAI clients that can be injected into agents.
"""

__all__ = ["OpenAIClients", "AsyncOpenAIClients"]


from dataclasses import dataclass
from typing import Mapping, Optional, Union

import openai
import instructor


@dataclass
class OpenAIClients:
    """
    A class that contains the OpenAI and Instructor clients.
    """

    openai: openai.OpenAI
    instructor: instructor.Instructor

    @classmethod
    def from_api_key(
        cls,
        api_key: str,
        base_url: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> "OpenAIClients":
        """Creates our OpenAI clients from an API key"""
        # Create two versions so that we can use the instructor client for
        # structured output and the openai client for everything else.
        # We duplicate the inner OpenAI client in case Instructor mutates it.
        obj = cls(
            openai=openai.OpenAI(
                api_key=api_key, base_url=base_url, default_headers=default_headers
            ),
            instructor=instructor.from_openai(
                openai.OpenAI(
                    api_key=api_key, base_url=base_url, default_headers=default_headers
                )
            ),
        )
        return obj

    def set_base_url(self, base_url: Union[str, None]) -> None:
        """Set the API base URL for the openai client"""
        # the OpenAI class has a property setter that expects either an
        # `httpx.URL` or a `str`, but mypy gets confused.
        self.openai.base_url = base_url  # type: ignore
        instructor_client = self.instructor.client
        if instructor_client is not None:
            instructor_client.base_url = base_url


@dataclass
class AsyncOpenAIClients:
    """
    A class that contains the OpenAI and Instructor clients.
    """

    openai: openai.AsyncOpenAI
    instructor: instructor.AsyncInstructor

    @classmethod
    def from_api_key(
        cls,
        api_key: str,
        base_url: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> "AsyncOpenAIClients":
        """Creates our OpenAI clients from an API key"""
        # Create two versions so that we can use the instructor client for
        # structured output and the openai client for everything else.
        # We duplicate the inner OpenAI client in case Instructor mutates it.
        obj = cls(
            openai=openai.AsyncOpenAI(
                api_key=api_key, base_url=base_url, default_headers=default_headers
            ),
            instructor=instructor.from_openai(
                openai.AsyncOpenAI(
                    api_key=api_key, base_url=base_url, default_headers=default_headers
                )
            ),
        )
        return obj

    def set_base_url(self, base_url: Union[str, None]) -> None:
        """Set the API base URL for the openai client"""
        # the OpenAI class has a property setter that expects either an
        # `httpx.URL` or a `str`, but mypy gets confused.
        self.openai.base_url = base_url  # type: ignore
        instructor_client = self.instructor.client
        if instructor_client is not None:
            instructor_client.base_url = base_url

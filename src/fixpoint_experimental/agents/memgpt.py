# This file contains code snippets from MemGPT
# licensed under the Apache License, Version 2.0.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modifications:
#
# - Dylan 2024-05-20: simplified message summarizer function to work outside of
#   the MemGPT project.

"""MemGPT summarization code"""

from dataclasses import dataclass
from typing import Any, List, Optional, Type, TypeVar, Union, overload

from pydantic import BaseModel

from fixpoint.workflows import WorkflowRun
from fixpoint.logging import logger
from fixpoint.agents import BaseAgent
from fixpoint.completions import ChatCompletionMessageParam, ChatCompletion


@dataclass
class MemGPTSummarizeOpts:
    """Options for how the MemGPT summarize function works."""

    agent: BaseAgent
    context_window: int


T = TypeVar("T", bound=BaseModel)


# TODO(dbmikus) allow system message prefixes + postfixes that are never summarized
class MemGPTSummaryAgent:
    """WIP Keep a linear history of messages and summarize it when it overflows

    This is a work-in-progress class
    """

    _messages: List[ChatCompletionMessageParam]

    def __init__(self, opts: MemGPTSummarizeOpts):
        self._opts = opts
        self._agent = opts.agent
        self._messages = []

    @overload
    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: None = None,
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRun] = None,
        **kwargs: Any,
    ) -> ChatCompletion[BaseModel]: ...

    @overload
    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: Type[T],
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRun] = None,
        **kwargs: Any,
    ) -> ChatCompletion[T]: ...

    def create_completion(
        self,
        *,
        messages: List[ChatCompletionMessageParam],
        response_model: Optional[Type[T]] = None,
        model: Optional[str] = None,
        workflow_run: Optional[WorkflowRun] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion[T], ChatCompletion[BaseModel]]:
        """Create a chat completion, using historical (maybe summarized) messages in context"""
        # check if old messages + new messages is too long
        context_check = _ContextLengthCheck.from_opts_and_messages(
            self._opts, messages=self._messages, extra_preserved_messages=messages
        )

        # if so, summarize old messages
        if context_check.too_long:
            summary = memgpt_summarize(
                self._opts, self._messages, extra_preserved_messages=messages
            )
            self._messages = [{"role": "system", "content": summary}]

        cmpl = self._opts.agent.create_completion(
            messages=self._messages + messages,
            model=model,
            workflow_run=workflow_run,
            response_model=response_model,
            **kwargs,
        )
        self._messages += messages + [
            {"role": "assistant", "content": cmpl.choices[0].message.content}
        ]
        return cmpl


@dataclass
class _ContextLengthCheck:
    summary_input: str
    summary_input_tkns: int
    too_long: bool

    @classmethod
    def from_opts_and_messages(
        cls,
        opts: MemGPTSummarizeOpts,
        messages: List[ChatCompletionMessageParam],
        extra_preserved_messages: Optional[List[ChatCompletionMessageParam]] = None,
    ) -> "_ContextLengthCheck":
        """Create a _ContextLengthCheck from a set of messages"""
        if extra_preserved_messages:
            all_messages = messages + extra_preserved_messages
        else:
            all_messages = messages
        summary_input = _format_summary_history(all_messages)
        summary_input_tkns = opts.agent.count_tokens(summary_input)

        # If we had too many messages such that we exceeded the context window,
        # recursively summarize older messages until we are under the limit.
        too_long = (
            summary_input_tkns > MESSAGE_SUMMARY_WARNING_FRAC * opts.context_window
        )

        return _ContextLengthCheck(summary_input, summary_input_tkns, too_long)


# From (with modifications):
# https://github.com/cpacker/MemGPT/blob/1e1ba5ed211b20f7535c83e0a6f7050658240ed9/memgpt/memory.py#L116
def memgpt_summarize(
    opts: MemGPTSummarizeOpts,
    messages: List[ChatCompletionMessageParam],
    extra_preserved_messages: Optional[List[ChatCompletionMessageParam]] = None,
    insert_acknowledgement_assistant_message: bool = True,
) -> str:
    """Use AI to summarize messages outside the context window

    If the messages exceed the LLM's context window, use an LLM to summarize the
    excess messages. The `messages` list is ordered so that newer messages are
    at the end of the list.

    `extra_preserved_messages` are messages that should not be summarized, but
    should be taken into account when checking if we have exceeded the context
    window and need to summarize.

    `insert_acknowledgement_assistant_message` controls whether to insert an
    acknowledgement assistant message in the summarization.
    """
    context_window = opts.context_window
    summary_prompt = SUMMARY_PROMPT_SYSTEM

    context_check = _ContextLengthCheck.from_opts_and_messages(
        opts, messages, extra_preserved_messages
    )
    summary_input = context_check.summary_input
    summary_input_tkns = context_check.summary_input_tkns

    # If we had too many messages such that we exceeded the context window,
    # recursively summarize older messages until we are under the limit.
    if context_check.too_long:
        logger.info("Context too large. Summarizing the message history.")
        trunc_ratio = (
            MESSAGE_SUMMARY_WARNING_FRAC * context_window / summary_input_tkns
        ) * 0.8  # For good measure...
        cutoff = int(len(messages) * trunc_ratio)
        summary_input = str(
            [memgpt_summarize(opts, messages=messages[:cutoff])] + messages[cutoff:]
        )

    # This actually summarizes the old messages

    message_sequence: List[ChatCompletionMessageParam] = []
    message_sequence.append({"role": "system", "content": summary_prompt})
    if insert_acknowledgement_assistant_message:
        message_sequence.append(
            {"role": "assistant", "content": MESSAGE_SUMMARY_REQUEST_ACK}
        )
    message_sequence.append({"role": "user", "content": summary_input})

    completion = opts.agent.create_completion(
        messages=message_sequence,
    )
    # technically, the content could be empty, but in practice it will not be
    return completion.choices[0].message.content or ""


def _format_summary_history(message_history: List[ChatCompletionMessageParam]) -> str:
    return "\n".join([f"{m['role']}: {m['content']}" for m in message_history])


# The amount of tokens before a sytem warning about upcoming truncation is sent
# to MemGPT
MESSAGE_SUMMARY_WARNING_FRAC = 0.75

WORD_LIMIT = 100
SUMMARY_PROMPT_SYSTEM = f"""
Your job is to summarize a history of previous messages in a conversation between an AI persona and a human.
The conversation you are given is a from a fixed context window and may not be complete.
Messages sent by the AI are marked with the 'assistant' role.
The AI 'assistant' can also make calls to functions, whose outputs can be seen in messages with the 'function' role.
Things the AI says in the message content are considered inner monologue and are not seen by the user.
The only AI messages seen by the user are from when the AI uses 'send_message'.
Messages the user sends are in the 'user' role.
The 'user' role is also used for important system events, such as login events and heartbeat events (heartbeats run the AI's program without user action, allowing the AI to act without prompting from the user sending them a message).
Summarize what happened in the conversation from the perspective of the AI (use the first person).
Keep your summary less than {WORD_LIMIT} words, do NOT exceed this word limit.
Only output the summary, do NOT include anything else in your output.
"""

# The acknowledgement message used in the summarize sequence
MESSAGE_SUMMARY_REQUEST_ACK = "Understood, I will respond with a summary of the message (and only the summary, nothing else) once I receive the conversation history. I'm ready."  # pylint: disable=line-too-long

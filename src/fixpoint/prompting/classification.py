"""Prompting for classifying user messages"""

import json
from typing import Any, Dict, List, Optional, TypedDict

import jinja2
from pydantic import BaseModel

from fixpoint.workflows import WorkflowRun
from ..completions import (
    ChatCompletionMessageParam,
    ChatCompletion,
    ChatCompletionToolParam,
)
from ..agents import BaseAgent, CacheMode
from ..utils.messages import umsg


class Choice(TypedDict):
    """A classification choice"""

    choice: str
    description: str


_cot_classify_chain_of_thought_template = jinja2.Template(
    """
    First, write out in a step by step manner your reasoning to be sure that
    your conclusion is correct. Avoid simply stating the correct answer at the
    outset. Then print only a single choice from {{choices}} (without quotes or
    punctuation) on its own line corresponding to the correct answer
    """,
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
)


COT_CLASSIFY_TOOL_NAME = "cot_classify"


def _make_cot_classify_tool(choices: List[Choice]) -> ChatCompletionToolParam:
    cot_desc = _cot_classify_chain_of_thought_template.render(choices=choices)
    tools: ChatCompletionToolParam = {
        "type": "function",
        "function": {
            "name": COT_CLASSIFY_TOOL_NAME,
            "description": "Classify the eval and do chain of thought",
            "parameters": {
                "type": "object",
                "properties": {
                    "chain_of_thought": {
                        "type": "string",
                        "description": cot_desc,
                    },
                    "classification": {
                        "type": "string",
                        "anyOf": _make_cot_classes(choices),
                    },
                },
                "required": ["classification", "chain_of_thought"],
            },
        },
    }
    return tools


def _make_cot_classes(choices: List[Choice]) -> List[Dict[str, Any]]:
    return [
        {
            "type": "string",
            "enum": [choice["choice"]],
            "description": choice["description"],
        }
        for choice in choices
    ]


# TODO(dbmikus) make this a subclass of ChatCompletion for API consistency
class ClassifiedChatCompletion:
    """A classified chat completion"""

    completion: ChatCompletion[BaseModel]
    chain_of_thought: str
    classification: str

    def __init__(self, completion: ChatCompletion[BaseModel]):
        self.completion = completion
        tool_calls = completion.choices[0].message.tool_calls
        if tool_calls is None:
            raise ValueError("No tool calls found in the completion")
        fcall = tool_calls[0].function
        args = json.loads(fcall.arguments)
        self.chain_of_thought = args["chain_of_thought"]
        self.classification = args["classification"]


def classify_message(
    agent: BaseAgent,
    choices: List[Choice],
    user_message: str,
    *,
    context_messages: Optional[List[ChatCompletionMessageParam]] = None,
    model: Optional[str] = None,
    workflow_run: Optional[WorkflowRun] = None,
    cache_mode: Optional[CacheMode] = None
) -> ChatCompletion[BaseModel]:
    """Classify a user message

    agent: the agent to use for the classification
    model: the optional model (agents have a pre-set model, but you can override it)
    choices: the classification choices
    user_message: the user message to classify
    context_messages: the optional context messages to prepend to the user message
    workflow_run: the workflow run to use for the classification
    """
    tools = [_make_cot_classify_tool(choices)]
    # clone the list so we can modify it
    messages: List[ChatCompletionMessageParam] = []
    if context_messages:
        messages = list(context_messages)
    messages.append(umsg(user_message))

    return agent.create_completion(
        workflow_run=workflow_run,
        model=model,
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": COT_CLASSIFY_TOOL_NAME}},
        cache_mode=cache_mode,
    )


def create_classified_chat_completion(
    agent: BaseAgent,
    choices: List[Choice],
    user_message: str,
    *,
    context_messages: Optional[List[ChatCompletionMessageParam]] = None,
    model: Optional[str] = None,
    workflow_run: Optional[WorkflowRun] = None,
    cache_mode: Optional[CacheMode] = None
) -> ClassifiedChatCompletion:
    """Create a classified chat completion"""
    completion = classify_message(
        agent=agent,
        choices=choices,
        user_message=user_message,
        model=model,
        workflow_run=workflow_run,
        context_messages=context_messages,
        cache_mode=cache_mode,
    )
    return ClassifiedChatCompletion(completion=completion)

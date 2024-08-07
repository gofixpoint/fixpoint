"""The steps in a form agent workflow"""

from enum import Enum
from typing import List

import jinja2

from fixpoint.prompting import classification
from fixpoint.utils.messages import smsg
from fixpoint.workflows.imperative import WorkflowContext

from ._shared import SYSTEM_PREFIX


class FormType(Enum):
    """The type of form that the user is trying to create"""

    INVOICE = "invoice"
    EVENT_REGISTRATION = "event registration (ticketing)"
    UNKNOWN = "unknown"


_FORM_TYPE_CHOICES: List[classification.Choice] = [
    {
        "choice": FormType.INVOICE.value,
        "description": (
            "An invoice is used when the user is trying to send a form that "
            "requests payment for a service rendered, or otherwise invoice "
            "someone else."
        ),
    },
    {
        "choice": FormType.EVENT_REGISTRATION.value,
        "description": (
            "An event registration form (aka a ticketing form) is used when "
            "having users sign up for an event, or buy a ticket to an event."
        ),
    },
    {
        "choice": FormType.UNKNOWN.value,
        "description": ("You could not classify the form type into any other type."),
    },
]


_INTAKE_PROMPT = jinja2.Template(
    """
{{system_prefix}}

{{instructions}}
""",
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
).render(
    system_prefix=SYSTEM_PREFIX,
    instructions=(
        "You help users create interactive forms. You ask them what they are"
        " trying to do, and then you determine the best type of form they"
        " should use."
    ),
)


def classify_form_type(
    wfctx: WorkflowContext,
    user_message: str,
) -> FormType:
    """A workflow step that classifies the users message intent into a form type"""
    completion = classification.create_classified_chat_completion(
        agent=wfctx.agents["main"],
        choices=_FORM_TYPE_CHOICES,
        user_message=user_message,
        context_messages=[smsg(_INTAKE_PROMPT)],
    )

    match completion.classification:
        case FormType.INVOICE.value:
            return FormType.INVOICE
        case FormType.EVENT_REGISTRATION.value:
            return FormType.EVENT_REGISTRATION
        case FormType.UNKNOWN.value:
            return FormType.UNKNOWN
        case _:
            wfctx.logger.error("Unkown form type: %s", completion.classification)
            return FormType.UNKNOWN

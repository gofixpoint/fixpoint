"""The form agent step to questions about creating an invoice"""

from typing import Optional, Tuple, List

from pydantic import BaseModel, Field

from fixpoint.completions import ChatCompletion, ChatCompletionMessageParam

from fixpoint_extras.workflows.imperative import WorkflowContext
from ..controllers.infogather import InfoGatherer
from ._shared import SYSTEM_PREFIX


class InvoiceQuestions(BaseModel):
    """Questions to ask the user about the invoice they are creating."""

    # The invoice amount
    invoice_amount: Optional[float] = Field(
        default=None, description="The invoice amount, in dollars."
    )

    invoice_recipient_name: Optional[str] = Field(
        default=None,
        description=(
            "The full name of the person who is receiving the invoice "
            "(their full legal name, which usually has a first and last name)."
        ),
    )

    invoice_recipient_email: Optional[str] = Field(
        default=None,
        description="The email of the person who is receiving the invoice.",
    )

    invoice_purpose: Optional[str] = Field(
        default=None, description="The purpose of the invoice."
    )


def gather_invoice_info(
    wfctx: WorkflowContext,
    info_gatherer: InfoGatherer[InvoiceQuestions],
    user_message: str,
) -> Tuple[InvoiceQuestions, ChatCompletion[InvoiceQuestions]]:
    """Gather the invoice information from the user."""
    completion = info_gatherer.process_messages(
        _make_invoice_msgs(user_message),
        agent=wfctx.agents['main'],
    )
    sout = _validate_completion(completion)
    return sout, completion


def answer_invoice_questions(
    wfctx: WorkflowContext, user_message: str
) -> Tuple[InvoiceQuestions, ChatCompletion[InvoiceQuestions]]:
    """Answer the questions about the invoice."""
    completion = wfctx.agents['main'].create_completion(
        messages=_make_invoice_msgs(user_message),
        response_model=InvoiceQuestions,
    )
    sout = _validate_completion(completion)
    return sout, completion


def _validate_completion(
    completion: ChatCompletion[InvoiceQuestions],
) -> InvoiceQuestions:
    """Validate the completion and return the invoice questions."""
    sout = completion.fixp.structured_output
    if sout is None:
        raise ValueError("No structured output found")
    if not isinstance(sout, InvoiceQuestions):
        raise ValueError("Structured output is not an instance of InvoiceQuestions")
    return sout


def _make_invoice_msgs(user_msg: str) -> List[ChatCompletionMessageParam]:
    return [
        {"role": "system", "content": SYSTEM_PREFIX},
        {"role": "user", "content": user_msg},
    ]

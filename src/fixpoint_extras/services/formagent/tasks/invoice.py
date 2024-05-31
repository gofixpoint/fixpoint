"""The form agent step to questions about creating an invoice"""

from typing import Optional, Tuple

from pydantic import BaseModel, Field

from fixpoint.completions import ChatCompletion

from ..workflowcontext import WorkflowContext
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


def answer_invoice_questions(
    wfctx: WorkflowContext, user_message: str
) -> Tuple[InvoiceQuestions, ChatCompletion[InvoiceQuestions]]:
    """Answer the questions about the invoice."""
    completion = wfctx.agent.create_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PREFIX},
            {"role": "user", "content": user_message},
        ],
        response_model=InvoiceQuestions,
    )
    sout = completion.fixp.structured_output
    if sout is None:
        raise ValueError("No structured output found")
    if not isinstance(sout, InvoiceQuestions):
        raise ValueError("Structured output is not an instance of InvoiceQuestions")
    return sout, completion

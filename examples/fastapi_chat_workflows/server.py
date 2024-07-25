"""
Local server for the form agent.

The code below is a chatbot form wizard that collects information
from a user to generate an invoice or event registration form.
In this case, we have a product that lets users generate:
- invoices for billing customers
- ticketing forms for selling event tickets

The agent:
- Asks a user what they are trying to do and then classifies their intent
- Asks follow up questions it needs to construct either the invoice or the ticketing form

Fixpoint handles a few things here for you:
- We remember the information the human sent to the agent over
the course of their chat
- We progressively fill out "structured data forms" with the
unstructured text content the user messages the agent
having an LLM generate structured data makes it easy for the rest of
your program to parse LLM output

You can run this FastAPI app by running `./bin/fastapi-server` from repo's root directory.
"""

import os
from typing import cast
from fastapi import FastAPI, HTTPException

import fixpoint
from fixpoint.agents.openai import OpenAIClients
from fixpoint.workflows.imperative import (
    Workflow,
    WorkflowRun,
    WorkflowContext,
    Form,
)
from fixpoint.workflows.node_state import WorkflowStatus
from fixpoint_extras.analyze.memory import DataframeMemory

from .tasks import classify_form_type, FormType, gather_invoice_info, InvoiceQuestions
from .controllers.infogather import InfoGatherer


app = FastAPI()

_openai_key = os.getenv("OPENAI_API_KEY")
if not _openai_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set or is empty")

_wfagent = fixpoint.agents.OpenAIAgent(
    agent_id="main",
    model_name="gpt-3.5-turbo",
    openai_clients=OpenAIClients.from_api_key(_openai_key),
    memory=DataframeMemory(),
)
_wf = Workflow(id="test_workflow")


@app.post("/workflow_runs")
def create_workflow_run() -> WorkflowRun:
    """Create a new workflow run."""
    wfrun = _wf.run()

    # Define some state that we can use to keep track of number of interactions for a user
    wfrun.state.update({"max_interactions": 3, "num_interactions": 0})
    return wfrun


@app.post("/workflow_runs/{workflow_run_id}/chats")
def create_chat(workflow_run_id: str, user_message: str) -> str:
    """Create a chat for a workflow run."""
    wfctx = get_workflow_context(workflow_run_id)
    task = wfctx.workflow_run.node_info.task
    if task == "__main__":
        return classify_task(wfctx, user_message)
    elif task == FormType.INVOICE.value:
        return invoice_task(wfctx, user_message)
    elif task == FormType.EVENT_REGISTRATION.value:
        raise HTTPException(
            status_code=400, detail="Event registration task currently not supported"
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported task")


def classify_task(wfctx: WorkflowContext, user_message: str) -> str:
    """Classify the task for a workflow run."""
    form_type = classify_form_type(wfctx, user_message)
    if form_type == FormType.INVOICE:
        wfctx.workflow_run.goto_task(task_id=FormType.INVOICE.value)
        return "Could you please tell me more about the invoice?"
    elif form_type == FormType.EVENT_REGISTRATION:
        wfctx.workflow_run.goto_task(task_id=FormType.EVENT_REGISTRATION.value)
        return "Could you please tell me more about event registration?"

    return "Could you please clarify what you need help with?"


def get_workflow_context(workflow_run_id: str) -> WorkflowContext:
    """Get the workflow context for a workflow run."""
    wfrun = _wf.load_run(workflow_run_id)
    if wfrun is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    return WorkflowContext(wfrun, [_wfagent])


def invoice_task(wfctx: WorkflowContext, user_message: str) -> str:
    """Handle the invoice task for a workflow run."""
    wfrun = wfctx.workflow_run
    wfrun.state.update({"num_interactions": wfrun.state["num_interactions"] + 1})

    form_id = "invoice_questions"
    stored_form = wfrun.forms.get(form_id=form_id)

    if stored_form is None:
        form = Form[InvoiceQuestions](
            id=form_id,
            workflow_run_id=wfrun.id,
            workflow_id=wfrun.workflow_id,
            form_schema=InvoiceQuestions,
        )
    else:
        form = cast(Form[InvoiceQuestions], stored_form)

    # TODO(jakub): This is going to call info_gatherer.make_field_questions on every call.
    # A better approach would be some way to have a single instance of the
    # generated questions that you can load into the InfoGatherer.
    info_gatherer = InfoGatherer[InvoiceQuestions](
        form=form,
        agent=wfctx.agents["main"],
    )

    gather_invoice_info(wfctx, info_gatherer, user_message)

    if stored_form is None:
        wfrun.forms.store(form_id=form_id, schema=InvoiceQuestions)
    wfrun.forms.update(form_id=form_id, contents=info_gatherer.form.contents)

    if info_gatherer.is_complete():
        return f"Here is your form:\n\n{info_gatherer.form.contents.model_dump_json()}"

    task_id = wfrun.node_info.id
    while wfrun.state["num_interactions"] > wfrun.state["max_interactions"]:
        curr_form = wfrun.forms.get(form_id=form_id)
        if curr_form is None:
            raise HTTPException(
                status_code=400, detail="Unexpected error. Form not found."
            )
        task_entry_id = wfrun.state.get("task_entry_id")
        if task_entry_id is None:
            task_entry = wfrun.human.send_task_entry(task_id, curr_form.contents)
            wfrun.state.update({"task_entry_id": task_entry.id})
            return (
                "Looks like you're having trouble with your invoice. "
                "A real person has been notified to help you out! "
                "Check back in a few short moments!"
            )
        else:
            current_human_task = wfrun.human.get_task_entry(
                task_entry_id, curr_form.contents
            )
            if current_human_task is None:
                raise HTTPException(
                    status_code=400, detail="Unexpected error. Human task not found."
                )

            if current_human_task.status == WorkflowStatus.COMPLETED.value:
                updated_form_contents = current_human_task.to_original_model()
                wfrun.forms.update(form_id=form_id, contents=updated_form_contents)
                return (
                    f"A real person is done reviewing your form. Here it is:\n\n"
                    f"{updated_form_contents.model_dump_json()}"
                )
            else:
                return "A real person is working hard on fixing it. Please check back later!"

    more_questions = info_gatherer.format_questions()
    return more_questions

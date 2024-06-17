"""Local server for the form agent."""

import os
from typing import cast
from fastapi import FastAPI, HTTPException
from fixpoint_extras.services.formagent.setup import get_workflow_agent
from fixpoint_extras.workflows.imperative import (
    Workflow,
    WorkflowRun,
    WorkflowContext,
    Form,
)
from fixpoint_extras.services.formagent.tasks import (
    classify_form_type,
    FormType,
    gather_invoice_info,
    InvoiceQuestions,
)
from fixpoint_extras.services.formagent.controllers.infogather import InfoGatherer


app = FastAPI()

_openai_key = os.getenv("OPENAI_API_KEY")
if not _openai_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set or is empty")

_wfagent = get_workflow_agent(
    openai_key=_openai_key,
    model_name="gpt-3.5-turbo",  # TODO(jakub): Pass this as an env variable
)
_wf = Workflow(id="test_workflow")


@app.post("/workflow_runs")
def create_workflow_run() -> WorkflowRun:
    """Create a new workflow run."""
    return _wf.run()


@app.post("/workflow_runs/{workflow_run_id}/chats")
def create_chat(workflow_run_id: str, user_message: str) -> str:
    """Create a chat for a workflow run."""
    wfctx = get_workflow_context(workflow_run_id)
    task = wfctx.workflow_run.node_state.task
    if task == "__main__":
        # Classify the task on an initial message
        return classify_task(wfctx, user_message)

    # Check that the workflow state has progressed
    task = wfctx.workflow_run.node_state.task

    if task == FormType.INVOICE.value:
        return invoice_task(wfctx, user_message)
    elif task == FormType.EVENT_REGISTRATION.value:
        raise HTTPException(
            status_code=400, detail="Event registration task currently not supported"
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported task")


def classify_task(wfctx: WorkflowContext, user_message: str) -> str:
    """Classify the task for a workflow run."""
    form_type, _ = classify_form_type(wfctx, user_message)
    if form_type == FormType.INVOICE:
        wfctx.workflow_run.goto_task(task_id=FormType.INVOICE.value)
        return "Could you please tell me more about the invoice?"
    elif form_type == FormType.EVENT_REGISTRATION:
        wfctx.workflow_run.goto_task(task_id=FormType.EVENT_REGISTRATION.value)
        return "Could you please tell me more about event registration?"

    return "Could you please clarify what you need help with?"


def get_workflow_context(workflow_run_id: str) -> WorkflowContext:
    """Get the workflow context for a workflow run."""
    # Load workflow run using provided identifier
    wfrun = _wf.load_run(workflow_run_id)
    if wfrun is None:
        # When a workflow run is not found, inform the client
        raise HTTPException(status_code=404, detail="Workflow run not found")

    # Instantiate workflow context and use agent memory
    return WorkflowContext.from_workflow(wfrun, [_wfagent])


def invoice_task(wfctx: WorkflowContext, user_message: str) -> str:
    """Handle the invoice task for a workflow run."""
    wfrun = wfctx.workflow_run
    form_id = "invoice_questions"
    stored_form = wfrun.forms.get(form_id=form_id)

    # Create a Form for invoice questions
    if stored_form is None:
        form = Form[InvoiceQuestions](
            id=form_id,
            workflow_run_id=wfrun.id,
            form_schema=InvoiceQuestions,
        )
    else:
        form = cast(Form[InvoiceQuestions], stored_form)

    # Instantiate info gatherer
    # TODO(jakub): This is going to call info_gatherer.make_field_questions on every call.
    # A better approach would be some way to have a single instance of the
    # generated questions that you can load into the InfoGatherer.
    info_gatherer = InfoGatherer[InvoiceQuestions](
        form=form,
        agent=wfctx.agents["main"],
    )

    gather_invoice_info(wfctx, info_gatherer, user_message)

    # Store document
    if stored_form is None:
        wfrun.forms.store(form_id=form_id, schema=InvoiceQuestions)
    wfrun.forms.update(form_id=form_id, contents=info_gatherer.form.contents)

    # Get more information from info gatherer
    if info_gatherer.is_complete():
        return f"Here is your form:\n\n{info_gatherer.form.contents.model_dump_json()}"
    else:
        more_questions = info_gatherer.format_questions()
        return more_questions

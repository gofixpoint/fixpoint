"""FastAPI server for Fixpoint"""

from fastapi import FastAPI

app = FastAPI()


@app.post("/chat_completions")
async def create_chat_completion() -> None:
    """Create a chat completion."""


@app.post("/memories")
async def create_memory() -> None:
    """Create a memory."""


@app.get("/memories")
async def get_memories() -> None:
    """Get a list of memories."""


@app.post("/forms")
async def create_form() -> None:
    """Create a form."""


@app.get("/forms")
async def get_forms() -> None:
    """Get a list of forms."""


@app.post("/workflows")
async def create_workflow() -> None:
    """Create a workflow."""


@app.get("/workflows")
async def get_workflows() -> None:
    """Get a list of workflows."""


@app.get("/workflow-runs")
async def get_workflow_runs() -> None:
    """Get a list of workflow runs."""


@app.post("/workflow-runs")
async def create_workflow_run() -> None:
    """Create a workflow run."""

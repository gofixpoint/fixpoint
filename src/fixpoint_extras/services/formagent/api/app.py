from typing import Optional, Union

from fastapi import FastAPI
from pydantic import BaseModel

from fixpoint_extras.workflows import imperative


app = FastAPI()


class CreateMessageRequest(BaseModel):
    workflow_run_id: str
    task_id: str
    step_id: str
    message: str


class MessageResponse(BaseModel):
    workflow_run_id: str
    task_id: str
    step_id: str
    next_task_id: Optional[str] = None
    next_step_id: str
    message: str


class ThreadWorkflow(BaseModel):
    workflow_id: str
    workflow_run_id: str


@app.post("/threads/{workflow_id}/runs/")
def create_chat_thread_workflow(workflow_id: str) -> ThreadWorkflow:
    pass


@app.post("/messages/")
def send_message(req: CreateMessageRequest) -> MessageResponse:
    pass


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

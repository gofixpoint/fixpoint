"""Fast API chat client for the fastapi_chat_workflows example."""

import httpx

HOST = "http://localhost:8000"


def get_wf_run_id() -> str:
    """Gets the workflow run id from the server."""
    r = httpx.post(f"{HOST}/workflow_runs")
    return str(r.json()["id"])


def send_chat_message(wf_run_id: str, msg: str) -> str:
    """Sends a chat message to the Fast API server and gets a response back"""
    r = httpx.post(
        f"{HOST}/workflow_runs/{wf_run_id}/chats", params={"user_message": msg}
    )
    return str(r.json())


def chat_loop(wf_run_id: str) -> None:
    """Chat loop for the client."""
    print(f"Starting chat session (wf_run_id={wf_run_id})")
    while True:
        user_request = input("🙂: ")
        bot_response = send_chat_message(wf_run_id, user_request)
        print(f"🤖: {bot_response}")


def main() -> None:
    """Main function for the chat client."""
    wf_run_id = get_wf_run_id()
    chat_loop(wf_run_id)


if __name__ == "__main__":
    main()

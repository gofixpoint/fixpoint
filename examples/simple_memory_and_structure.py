import os
from pydantic import BaseModel
import fixpoint
from fixpoint.agents.oai import OpenAI
from fixpoint.agents.openai import OpenAIClients

agent = OpenAI(
    agent_id="my-agent",
    openai_clients=OpenAIClients.from_api_key(os.environ["OPENAI_API_KEY"]),
    memory=fixpoint.memory.Memory()
)



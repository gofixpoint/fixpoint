"""A simple example with agent memory and structured output"""

import os
from pydantic import BaseModel, Field
import fixpoint
from fixpoint.agents.oai import OpenAI
from fixpoint.agents.openai import OpenAIClients


# Set up an on-disk cache in the /tmp/agent-cache directory.  The cache will
# remember past LLM inferences, and use the cached completions if they are in
# the cache, saving you time and money on LLM inference.
cache = fixpoint.cache.ChatCompletionDiskTLRUCache(
    ttl_s=60 * 60,
    size_limit_bytes=1024 * 1024 * 50,
    cache_dir="/tmp/agent-cache",
)

# Create an OpenAI-compatible agent that has:
#
# - memory: remember all past messages and responses this agent had
# - cache: a cache that can be shared between agents to save money and speed up
#   inference
#
# The create agent has the same interface as the OpenAI client, with a few extra
# methods tucked into `agent.fixp...`
agent = OpenAI(
    agent_id="my-agent",
    openai_clients=OpenAIClients.from_api_key(os.environ["OPENAI_API_KEY"]),
    memory=fixpoint.memory.Memory(),
    cache=cache,
)

# Make the LLM output structured data that conforms to this Pydantic model:


# pylint: disable=missing-class-docstring
class City(BaseModel):
    name: str = Field(description="The name of the city")
    country: str = Field(description="The country the city is in")
    population: int = Field(description="The population of the city")


# pylint: disable=missing-class-docstring
class CityList(BaseModel):
    cities: list[City]


completion = agent.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "What are the most populous cities in Europe?"},
    ],
    # specify your structured output format here
    response_model=CityList,
)

# Access the structured output, so the rest of your program can easily use the
# AI's response without writing your own parsing logic.
assert completion.fixp.structured_output is not None
for city in completion.fixp.structured_output.cities:
    print(f"{city.name}, {city.country} - population of {city.population}")


# Look at the agent's memories to see the past chats.
assert len(agent.fixp.memory.memories()) == 1
print("\n")
print(agent.fixp.memory.memories()[0].messages)
print(agent.fixp.memory.memories()[0].completion.choices[0].model_dump())

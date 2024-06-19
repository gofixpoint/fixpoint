import asyncio
from dataclasses import dataclass
import json
import os
from typing import List

from fixpoint.agents.openai import OpenAIClients, OpenAIAgent
from fixpoint.completions.chat_completion import ChatCompletionMessageParam
from fixpoint.cache import ChatCompletionTLRUCache
from fixpoint.analyze.memory import DataframeMemory
from fixpoint_extras.workflows.imperative import WorkflowRun, WorkflowContext
from fixpoint_extras.workflows import structured


def init_workflow_context(workflow_run: WorkflowRun) -> WorkflowContext:
    cache = ChatCompletionTLRUCache(
        maxsize=1000,
        ttl_s=60 * 60 * 24 * 30,
    )
    openaiclients = OpenAIClients(api_key=os.getenv("OPENAI_API_KEY"))
    memory = DataframeMemory()
    # TODO(dbmikus) expose memory on an agent
    gpt3 = OpenAIAgent(
        model_name="gpt-3.5-turbo",
        openai_clients=openaiclients,
        memory=memory,
        cache=cache,
    )
    gpt4 = OpenAIAgent(
        model_name="gpt-4-turbo",
        openai_clients=openaiclients,
        memory=DataframeMemory(),
        cache=cache,
    )
    return WorkflowContext.from_workflow(
        workflow_run,
        agents={"gpt3": gpt3, "gpt4": gpt4},
        # TODO(dbmikus) remove this and require users to pull the memory off the agents
        memory=memory,
        cache=cache,
    )


@structured.workflow(id="example_workflow", ctx_factory=init_workflow_context)
class CompareModels:
    structured.entrypoint()
    async def run(self, ctx: WorkflowContext, prompts: List[List[ChatCompletionMessageParam]]) -> None:
        gpt3_res = structured.spawn(RunAllPrompts, args=[RunAllPromptsArgs(agent_name="gpt3", prompts=prompts)])
        gpt4_res = structured.spawn(RunAllPrompts, args=[RunAllPromptsArgs(agent_name="gpt4", prompts=prompts)])

        results = {
            "gpt3": gpt3_res,
            "gpt4": gpt4_res
        }
        # TODO(dbmikus) this is not async, so it will block the async event loop
        ctx.workflow_run.docs.store(
            contents=json.dumps(results)
        )


@dataclass
class RunAllPromptsArgs:
    agent_name: str
    prompts: List[List[ChatCompletionMessageParam]]


@structured.task(id="run_all_prompts")
class RunAllPrompts:
    @structured.entrypoint()
    async def run_all_prompts(ctx: WorkflowContext, args: RunAllPromptsArgs) -> List[str]:
        step_results = []
        for prompt in args.prompts:
            step_results.append(
                structured.call(
                    run_prompt,
                    args=[RunPromptArgs(agent_name=args.agent_name, prompt=prompt)],
                )
            )
        return await asyncio.gather(*step_results)


@dataclass
class RunPromptArgs:
    agent_name: str
    prompt: List[ChatCompletionMessageParam]


@structured.step(id="run_prompt")
def run_prompt(ctx: WorkflowContext, args: RunPromptArgs) -> str:
    agent = ctx.agents[args.agent_name]
    return agent.create_completion(messages=args.prompt)


if __name__ == "__main__":
    structured.run_workflow(CompareModels, [])

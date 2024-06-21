import asyncio
from dataclasses import dataclass
import json
import os
from typing import Awaitable, List, Union

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
    openaiclients = OpenAIClients.from_api_key(api_key=os.environ["OPENAI_API_KEY"])
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
    @structured.workflow_entrypoint()
    async def run(
        self, ctx: WorkflowContext, prompts: List[List[ChatCompletionMessageParam]]
    ) -> None:
        gpt3_res = structured.call_task(
            ctx,
            RunAllPrompts.run_all_prompts,
            args=[RunAllPromptsArgs(agent_name="gpt3", prompts=prompts)],
        )
        gpt4_res = structured.call_task(
            ctx,
            RunAllPrompts.run_all_prompts,
            args=[RunAllPromptsArgs(agent_name="gpt4", prompts=prompts)],
        )

        results = {"gpt3": await gpt3_res, "gpt4": await gpt4_res}
        # TODO(dbmikus) this is not async, so it will block the async event loop
        ctx.workflow_run.docs.store(id="inference-results.json", contents=json.dumps(results))


@dataclass
class RunAllPromptsArgs:
    agent_name: str
    prompts: List[List[ChatCompletionMessageParam]]


@structured.task(id="run_all_prompts")
class RunAllPrompts:
    @structured.task_entrypoint()
    async def run_all_prompts(self, ctx: WorkflowContext, args: RunAllPromptsArgs) -> List[Union[str, None]]:
        step_results: List[Awaitable[Union[str, None]]] = []
        for prompt in args.prompts:
            step_results.append(
                structured.call_step(
                    ctx,
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
async def run_prompt(ctx: WorkflowContext, args: RunPromptArgs) -> Union[str, None]:
    agent = ctx.agents[args.agent_name]
    completion = agent.create_completion(messages=args.prompt)
    return completion.choices[0].message.content


if __name__ == "__main__":
    asyncio.run(structured.run_workflow(CompareModels.run, []))

"""An example of Fixpoint's structured LLM workflows."""

import asyncio
from dataclasses import dataclass
import json
import os
from typing import List, Union, Dict

from fixpoint.agents.openai import OpenAIClients, OpenAIAgent
from fixpoint.completions.chat_completion import ChatCompletionMessageParam
from fixpoint.cache import ChatCompletionTLRUCache
from fixpoint.analyze.memory import DataframeMemory
from fixpoint_extras.workflows.imperative import WorkflowRun, WorkflowContext
from fixpoint_extras.workflows import structured


def init_workflow_context(workflow_run: WorkflowRun) -> WorkflowContext:
    """Factory function to initialize a workflow context for a workflow definition"""

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
        cache=cache,
    )


@structured.workflow(id="example_workflow", ctx_factory=init_workflow_context)
class CompareModels:
    """Compare the performance of GPT-3.5 and GPT-4"""

    @structured.workflow_entrypoint()
    async def run(
        self, ctx: WorkflowContext, prompts: List[List[ChatCompletionMessageParam]]
    ) -> None:
        """Entrypoint for the workflow to compare agents"""

        async with asyncio.TaskGroup() as tg:
            gpt3_res = tg.create_task(
                structured.call_task(
                    ctx,
                    RunAllPrompts.run_all_prompts,
                    args=[RunAllPromptsArgs(agent_name="gpt3", prompts=prompts)],
                )
            )
            gpt4_res = tg.create_task(
                structured.call_task(
                    ctx,
                    RunAllPrompts.run_all_prompts,
                    args=[RunAllPromptsArgs(agent_name="gpt4", prompts=prompts)],
                )
            )

        results: Dict[str, List[Union[str, None]]] = {
            "gpt3": gpt3_res.result(),
            "gpt4": gpt4_res.result(),
        }
        # TODO(dbmikus) this is not async, so it will block the async event loop
        ctx.workflow_run.docs.store(
            id="inference-results.json", contents=json.dumps(results)
        )


@dataclass
class RunAllPromptsArgs:
    """Arguments for the "run_al_prompts" task"""

    agent_name: str
    prompts: List[List[ChatCompletionMessageParam]]


@structured.task(id="run_all_prompts")
class RunAllPrompts:
    """A task that runs all prompts for an agent"""

    @structured.task_entrypoint()
    async def run_all_prompts(
        self, ctx: WorkflowContext, args: RunAllPromptsArgs
    ) -> List[Union[str, None]]:
        """Execute all prompt inferences for an agent"""
        step_tasks: List[asyncio.Task[Union[str, None]]] = []
        async with asyncio.TaskGroup() as tg:
            for prompt in args.prompts:
                step_task = tg.create_task(
                    structured.call_step(
                        ctx,
                        run_prompt,
                        args=[RunPromptArgs(agent_name=args.agent_name, prompt=prompt)],
                    )
                )
                step_tasks.append(step_task)
        step_results = [task.result() for task in step_tasks]
        return step_results


@dataclass
class RunPromptArgs:
    """Args for run_prompt"""

    agent_name: str
    prompt: List[ChatCompletionMessageParam]


@structured.step(id="run_prompt")
async def run_prompt(ctx: WorkflowContext, args: RunPromptArgs) -> Union[str, None]:
    """Run an LLM inference request with the given agent and prompt"""
    agent = ctx.agents[args.agent_name]
    completion = agent.create_completion(messages=args.prompt)
    return completion.choices[0].message.content


if __name__ == "__main__":
    asyncio.run(
        structured.run_workflow(
            CompareModels.run,
            [
                [
                    [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "What is the meaning of life?"},
                    ],
                    [
                        {"role": "system", "content": "You are an evil AI."},
                        {"role": "user", "content": "What is the meaning of life?"},
                    ],
                ]
            ],
        )
    )

"""An example of Fixpoint's structured LLM workflows."""

import asyncio
from dataclasses import dataclass
import json
import os
from typing import List, Union, Dict, Tuple

from fixpoint.agents import BaseAgent
from fixpoint.agents.openai import OpenAIClients, OpenAIAgent
from fixpoint.completions.chat_completion import ChatCompletionMessageParam

from fixpoint_extras.workflows import structured
from fixpoint_extras.workflows.structured import WorkflowContext


@structured.workflow(id="example_workflow")
class CompareModels:
    """Compare the performance of GPT-3.5 and GPT-4"""

    @structured.workflow_entrypoint()
    async def run(
        self, ctx: WorkflowContext, prompts: List[List[ChatCompletionMessageParam]]
    ) -> str:
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
        doc_id = "inference-results.json"
        ctx.workflow_run.docs.store(id=doc_id, contents=json.dumps(results))
        return doc_id


# We recommend using a single dataclass, Pydantic model, or dictionary argument
# for the task. This makes it easy to add or remove arguments in the future
# while preserving backwards compatability.
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


def setup_agents() -> Tuple[structured.RunConfig, List[BaseAgent]]:
    """Setup agents for the workflow"""
    run_config = structured.RunConfig.with_defaults()
    openaiclients = OpenAIClients.from_api_key(api_key=os.environ["OPENAI_API_KEY"])
    gpt3 = OpenAIAgent(
        agent_id="gpt3",
        model_name="gpt-3.5-turbo",
        openai_clients=openaiclients,
        cache=run_config.storage.agent_cache,
    )
    gpt4 = OpenAIAgent(
        agent_id="gpt4",
        model_name="gpt-4-turbo",
        openai_clients=openaiclients,
        cache=run_config.storage.agent_cache,
    )
    return run_config, [gpt3, gpt4]


async def main() -> None:
    """configure and run the workflow"""
    run_config, agents = setup_agents()

    run_handle = structured.spawn_workflow(
        CompareModels.run,
        run_config=run_config,
        agents=agents,
        args=[
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
    print("Running workflow:", run_handle.workflow_id())
    print("Run ID:", run_handle.workflow_run_id())
    results_doc_id = await run_handle.result()
    print("finished workflow. Wrote results to workflow run doc:", results_doc_id)


if __name__ == "__main__":
    asyncio.run(main())

"""An example of Fixpoint's structured LLM workflows."""

import asyncio
from dataclasses import dataclass
from io import StringIO
import os
import tempfile
from typing import List, Union, Tuple

import pandas as pd

from fixpoint.agents import AsyncBaseAgent
from fixpoint.agents.openai import AsyncOpenAIClients, AsyncOpenAIAgent
from fixpoint.completions.chat_completion import ChatCompletionMessageParam
from fixpoint.workflows import structured
from fixpoint.workflows.structured import WorkflowContext


# A workflow is a Python class decorated with `@structured.workflow(id="...")`.
# The workflow ID lets you track and inspect multiple running instances of this
# workflow, called a `WorkflowRun`.
#
# Workflows run in the `asyncio` loop for better concurrency.
@structured.workflow(id="example_workflow")
class CompareModels:
    """Compare the performance of GPT-3.5 and GPT-4"""

    # A workflow definition must have exactly one entrypoint, and it must be an
    # async function.
    #
    # We recommend that you use one single extra argument, which should be
    # JSON-serializable. This makes it easy to add and remove fields to that
    # argument for backwards/forwards compatibilty.
    #
    # The first non-self argument is always the `WorkflowContext`, which tracks
    # the current WorkflowRun, and it contains a few things:
    #
    # - The `workflow_run` itself, with which you can inspect the current node
    #   state (what task and step are we in?), store and search documents scoped
    #   to the workflow, and fill out structured forms scoped to the workflow.
    # - The dictionary of `agents` in the workflow run. Each agent has memory
    #   for the life of the `WorkflowRun`.
    # - An optional `cache`, which stores cached agent inference requests, so
    #   you don't duplicate requests and spend extra money. You can access this
    #   to invalidate cache items or skip caching for certain steps.
    # - A logger that is scoped to the lifetime of the `WorkflowRun`.
    # - The `run_config`, that defines settings for the worflow run. You rarely
    #   need to access this.
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

        gpt3_resps: List[Union[str, None]] = []
        gpt4_resps: List[Union[str, None]] = []
        for gpt3_resp, gpt4_resp in zip(gpt3_res.result(), gpt4_res.result()):
            gpt3_resps.append(gpt3_resp[1])
            gpt4_resps.append(gpt4_resp[1])

        df = pd.DataFrame(
            {
                "prompt": prompts,
                "gpt3": gpt3_resps,
                "gpt4": gpt4_resps,
            }
        )

        # TODO(dbmikus) this is not async, so it will block the async event loop
        doc_id = "inference-results.json"
        ctx.workflow_run.docs.store(id=doc_id, contents=df.to_json(path_or_buf=None))
        return doc_id


PromptCompletionPair = Tuple[List[ChatCompletionMessageParam], Union[str, None]]


# We recommend using a single dataclass, Pydantic model, or dictionary argument
# for the task. This makes it easy to add or remove arguments in the future
# while preserving backwards compatability.
@dataclass
class RunAllPromptsArgs:
    """Arguments for the "run_al_prompts" task"""

    agent_name: str
    prompts: List[List[ChatCompletionMessageParam]]


# Defining a task is similar to defining a workflow. You decorate a class and
# then mark the task entrypoint. You can think of a task as a segment of your
# workflow, where your LLM (and normal code) is accomplishing some "task".
#
# The results of a task run are cached so that they can be made "durable". If
# your workflow has multiple tasks and you get all the way through the first
# task before failing on the second, the workflow will automatically restart and
# resume from after the first task.
@structured.task(id="run_all_prompts")
class RunAllPrompts:
    """A task that runs all prompts for an agent"""

    @structured.task_entrypoint()
    async def run_all_prompts(
        self, ctx: WorkflowContext, args: RunAllPromptsArgs
    ) -> List[PromptCompletionPair]:
        """Execute all prompt inferences for an agent

        Returns a list of (prompt, response) pairs.
        """
        step_tasks: List[asyncio.Task[PromptCompletionPair]] = []
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


# Steps are the smallest unit of computation that we track in a workflow. Of
# course, you can make a step composed of normal functions and other normal
# Python code, but steps are given durability and step-specific agent memory.
#
# Like tasks, steps are:


# - Durable, so if a workflow or task fails partway through and encounters a
#   step it already ran, it will use the previously computed result.
# - Have a `WorkflowContext` as the first argument.
# - Require that all subsequent arguments are serializable.
@structured.step(id="run_prompt")
async def run_prompt(ctx: WorkflowContext, args: RunPromptArgs) -> PromptCompletionPair:
    """Run an LLM inference request with the given agent and prompt

    Returns a pair of (prompt, response)
    """
    agent = ctx.agents[args.agent_name]
    ctx.logger.info("Running prompt with agent %s", args.agent_name)
    completion = await agent.create_completion(messages=args.prompt)
    return (args.prompt, completion.choices[0].message.content)


def setup_agents() -> Tuple[structured.RunConfig, List[AsyncBaseAgent]]:
    """Setup agents for the workflow"""
    run_config = structured.RunConfig.with_defaults()
    openaiclients = AsyncOpenAIClients.from_api_key(
        api_key=os.environ["OPENAI_API_KEY"]
    )
    gpt3 = AsyncOpenAIAgent(
        agent_id="gpt3",
        model_name="gpt-3.5-turbo",
        openai_clients=openaiclients,
        cache=run_config.storage.agent_cache,
    )
    gpt4 = AsyncOpenAIAgent(
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

    # You can load the doc into a dataframe and look at the results
    wrun = run_handle.finalized_workflow_run()
    if wrun is None:
        raise RuntimeError(
            "We awaited the workflow run and it finished,"
            " so we should have access to the WorkflowRun object."
        )
    doc = wrun.docs.get(results_doc_id)
    if doc is None:
        raise RuntimeError(f"Expected doc {results_doc_id} to exist, but it does not")
    df = pd.read_json(StringIO(doc.contents))
    print(df.head())

    # Create a temporary file to store the results
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json"
    ) as temp_file:
        df.to_json(temp_file.name, orient="records", indent=4)
        print(f"Results saved to temporary JSON file: {temp_file.name}")

    # Note: The temporary file will persist after the script ends.
    # You may want to add code to remove it later if it's no longer needed.


if __name__ == "__main__":
    asyncio.run(main())

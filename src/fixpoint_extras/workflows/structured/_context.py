"""The workflow context for structured workflows"""

import logging
from typing import List, Optional

from fixpoint.agents import BaseAgent
from fixpoint.cache import SupportsChatCompletionCache

from ..imperative import WorkflowContext as ImperativeWorkflowContext, WorkflowRun
from ._run_config import RunConfig


class WorkflowContext(ImperativeWorkflowContext):
    """A context for a structured workflow"""

    run_config: RunConfig

    def __init__(
        self,
        run_config: RunConfig,
        workflow_run: WorkflowRun,
        agents: List[BaseAgent],
        cache: Optional[SupportsChatCompletionCache] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(workflow_run, agents, cache, logger)
        self.run_config = run_config

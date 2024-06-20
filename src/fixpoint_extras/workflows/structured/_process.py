from typing import Any, Callable, Dict, List, Optional

from ._helpers import Params, Ret


def spawn(fn: Callable[Params, Ret], args: Optional[List[Any]], kwargs: Optional[Dict[str, Any]]) -> Ret:
    pass


def call(fn: Callable[Params, Ret], args: Optional[List[Any]], kwargs: Optional[Dict[str, Any]]) -> Ret:
    pass

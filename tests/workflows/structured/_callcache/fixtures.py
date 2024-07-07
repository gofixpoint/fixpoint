from dataclasses import dataclass
from typing import Dict, List

from pydantic import BaseModel


class PBMInner(BaseModel):
    key200: Dict[str, int]
    key100: int


class PBM(BaseModel):
    xyz: PBMInner
    abc: Dict[str, int]
    middle: List[str]


@dataclass
class DCInner:
    key200: Dict[str, int]
    key100: int


@dataclass
class DC:
    xyz: DCInner
    abc: Dict[str, int]
    middle: List[str]

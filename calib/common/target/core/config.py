from typing import Annotated, Literal
from pydantic import BaseModel, Field

class CheckerboardConfig(BaseModel):
    type: Literal["checkerboard"]
    rows: int
    cols: int
    checker_size_mm: float

class AprilgridConfig(BaseModel):
    type: Literal["aprilgrid"]
    rows: int
    cols: int
    family: str
    tag_size_mm: float
    tag_spacing_mm: float

TargetConfigType = Annotated[
    CheckerboardConfig | AprilgridConfig,
    Field(discriminator="type")
]

class TargetConfig(BaseModel):
    target: TargetConfigType
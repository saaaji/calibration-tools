from typing import Annotated, Literal, Optional, Union, get_args
from pydantic import BaseModel, Field

class OpenCvConfig(BaseModel):
    backend: Literal["cv"]
    device: int = 0
    fps: int = 30

class BaslerConfig(BaseModel):
    backend: Literal["basler"]
    serial: str
    trigger_line: Optional[int]

CameraConfig = Annotated[
    Union[OpenCvConfig, BaslerConfig],
    Field(discriminator="backend"),
]

class CameraArrayConfig(BaseModel):
    cameras: list[CameraConfig]
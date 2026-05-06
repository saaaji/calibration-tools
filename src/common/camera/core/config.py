from typing import Annotated, Literal
from pydantic import BaseModel, Field

class BaseCameraConfig(BaseModel):
    flip_horizontal: bool = False
    flip_vertical: bool = False
    width: int
    height: int

class OpenCvConfig(BaseCameraConfig):
    backend: Literal["cv"]
    device: int = 0
    fps: int = 30

class BaslerConfig(BaseCameraConfig):
    backend: Literal["basler"]
    serial: str
    trigger_line: int | None = None

CameraConfig = Annotated[
    OpenCvConfig | BaslerConfig,
    Field(discriminator="backend"),
]

class CameraArrayConfig(BaseModel):
    cameras: list[CameraConfig]
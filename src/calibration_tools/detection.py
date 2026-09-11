from dataclasses import dataclass
from typing import Protocol, Literal, Union, Annotated
from pydantic import BaseModel, Field
import cv2
import numpy as np
import ethz_apriltag2_python

# board abstraction


@dataclass(frozen=True)
class BoardSpec:
    rows: int
    cols: int
    spacing_m: float


class BoardDetector(Protocol):
    @property
    def board(self) -> BoardSpec: ...

    def detect(self, image: np.ndarray) -> np.ndarray | None:
        """return (rows, cols, 3) containing x,y,weight"""
        ...

    def draw_detection(
        self, image: np.ndarray, observation: np.ndarray | None
    ) -> np.ndarray: ...


# configs


class WeakCheckerboardConfig(BaseModel):
    type: Literal["weak_checkerboard"]
    rows: int
    cols: int
    spacing_m: float


# weak checkerboard


class WeakCheckerboardDetector:
    def __init__(self, config: WeakCheckerboardConfig):
        self._board = BoardSpec(
            rows=config.rows, cols=config.cols, spacing_m=config.spacing_m
        )
        self._target = ethz_apriltag2_python.Checkerboard(
            config.rows, config.cols, config.spacing_m, config.spacing_m
        )

    @property
    def board(self):
        return self._board

    def detect(self, image: np.ndarray) -> np.ndarray | None:
        valid, points, observed = self._target.detect(image)

        if not valid:
            return None

        points = points.reshape(self._board.rows, self._board.cols, 2)
        observed = observed.reshape(self._board.rows, self._board.cols)

        result = np.empty((*points.shape[:2], 3), dtype=np.float64)

        result[..., :2] = points
        result[..., 2] = np.where(observed, 1.0, -1.0)

        return result

    def draw_detection(
        self, image: np.ndarray, observation: np.ndarray | None
    ) -> np.ndarray:
        if image.ndim == 2:
            result = np.stack((image,) * 3, axis=-1)
        else:
            result = image.copy()

        if observation is None:
            return result

        rows, cols, _ = observation.shape

        for r in range(rows):
            for c in range(cols):
                x, y, weight = observation[r, c]

                if weight < 0:
                    continue

                p = (round(x), round(y))
                cv2.circle(result, p, 4, (0, 255, 0), -1)

        return result


# factory


DetectorConfig = Annotated[Union[WeakCheckerboardConfig], Field(discriminator="type")]


def make_detector(config: DetectorConfig) -> BoardDetector:
    match config:
        case WeakCheckerboardConfig():
            return WeakCheckerboardDetector(config)
        case _:
            raise ValueError(f"unknown detector config")

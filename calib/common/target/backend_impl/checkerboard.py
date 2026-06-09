import cv2
import numpy as np
from ..core.target import Target
from ..core.config import CheckerboardConfig

class Checkerboard(Target):
    class Detection(Target.Detection):
        def image_points(self) -> np.ndarray:
            # detected image points, shape (N, 2)
            pass

        def object_points(self) -> np.ndarray:
            # detected object points, shape (N, 3)
            pass

    def __init__(self, config: CheckerboardConfig):
        self.config = config

    def detect(self, frame: np.ndarray) -> "Target.Detection | None":
        pass

    def all_object_points(self) -> np.ndarray:
        pass
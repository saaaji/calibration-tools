import numpy as np
from abc import ABC, abstractmethod
from .config import TargetConfigType

class Target(ABC):
    class Detection(ABC):
        @abstractmethod
        def image_points(self) -> np.ndarray:
            # detected image points, shape (N, 2)
            pass

        @abstractmethod
        def object_points(self) -> np.ndarray:
            # detected object points, shape (N, 3)
            pass

    def __init__(self, config: TargetConfigType):
        self.config = config

    @abstractmethod
    def detect(self, frame: np.ndarray) -> "Target.Detection | None":
        pass

    @abstractmethod
    def all_object_points(self) -> np.ndarray:
        pass
import cv2
import numpy as np
from abc import ABC, abstractmethod
from .config import CameraConfig

class Camera(ABC):
    def __init__(self, config: CameraConfig):
        self.config = config

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def get_raw_frame(self) -> np.ndarray:
        pass

    def read(self) -> np.ndarray:
        frame = self.get_frame()

        if self.config.flip_horizontal and self.config.flip_vertical:
            return cv2.flip(frame, -1)
        if self.config.flip_horizontal:
            return cv2.flip(frame, 1)
        if self.config.flip_vertical:
            return cv2.flip(frame, 0)
        
        return frame

    @abstractmethod
    def release(self) -> None:
        pass
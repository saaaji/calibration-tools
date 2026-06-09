import cv2
import numpy as np
from ..core.camera import Camera
from ..core.config import OpenCvConfig

class OpenCvCamera(Camera):
    def __init__(self, config: OpenCvConfig):
        super().__init__(config)
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        # try to open
        self._cap = cv2.VideoCapture(self.config.device)
        if not self._cap.isOpened():
            raise RuntimeError(f"could not open camera {self.config.device}")
        
        # attributes
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.config.fps)

    def get_raw_frame(self) -> np.ndarray:
        if self._cap is None:
            raise RuntimeError(f"camera {self.config.device} is not opened")
        
        ok, frame = self._cap.read()
        if not ok:
            raise RuntimeError(f"failed to read from camera {self.config.device}")
        
        return frame
    
    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
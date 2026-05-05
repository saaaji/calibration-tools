from abc import ABC, abstractmethod
from .backends import CameraConfig, CameraArrayConfig

class Camera(ABC):
    def __init__(self, config: CameraConfig):
        self.config = config

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def read(self) -> None:
        pass

    @abstractmethod
    def release(self) -> None:
        pass



if __name__ == "__main__":
    import json
    from pydantic import TypeAdapter

    ex = """
    {
        "cameras": [
            {
                "backend": "basler",
                "serial": "test",
                "trigger_line": 3
            },
            {
                "backend": "cv",
                "device": 0
            }
        ]
    }
    """

    raw_cfg = json.loads(ex)
    cfg = CameraArrayConfig.model_validate(raw_cfg)

    print(cfg.__class__, cfg)
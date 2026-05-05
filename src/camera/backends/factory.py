from ..core.backends import CameraConfig
from .cv import OpenCvConfig, OpenCvCamera
from .basler import BaslerConfig, BaslerCamera

def instantiate(config: CameraConfig):
    if isinstance(config, OpenCvConfig):
        return OpenCvCamera(config)
    elif isinstance(config, BaslerConfig):
        return BaslerCamera(config)
    
    raise ValueError(f"unrecognized config: {config}")
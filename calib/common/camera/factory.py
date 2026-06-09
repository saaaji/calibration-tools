from .core.config import CameraConfig
from .backend_impl.cv import OpenCvConfig, OpenCvCamera
from .backend_impl.basler import BaslerConfig, BaslerCamera

def create_camera(config: CameraConfig):
    if isinstance(config, OpenCvConfig):
        return OpenCvCamera(config)
    elif isinstance(config, BaslerConfig):
        return BaslerCamera(config)
    
    raise ValueError(f"unrecognized config: {config}")
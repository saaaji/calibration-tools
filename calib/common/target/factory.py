from .core.config import TargetConfig
from .backend_impl.checkerboard import CheckerboardConfig, Checkerboard
from .backend_impl.aprilgrid import AprilgridConfig, Aprilgrid

def create_target(config: TargetConfig):
    if isinstance(config, CheckerboardConfig):
        return Checkerboard(config)
    elif isinstance(config, AprilgridConfig):
        return Aprilgrid(config)
    
    raise ValueError(f"unrecognized config: {config}")
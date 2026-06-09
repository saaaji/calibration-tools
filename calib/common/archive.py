import secrets
import tomlkit
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from .camera.core.config import CameraConfig
from .target.core.config import TargetConfigType

class ArchiveManifest(BaseModel):
    tag: str
    created: datetime
    target: TargetConfigType
    extrinsics: bool

    @classmethod
    def create(cls, archive_dir: Path, rig: list[CameraConfig], target_config: TargetConfigType, extrinsics: bool = False, tag: str | None = None) -> "ArchiveManifest":
        manifest = cls(
            tag=tag if tag is not None else secrets.token_hex(4), 
            created=datetime.now(),
            target_config=target_config,
            extrinsics=extrinsics,
        )

    @property
    def name(self) -> str:
        return f"calib_{self.tag}"

    def save(self, archive_dir: Path) -> None:
        path = archive_dir / self.name / "manifest.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tomlkit.dumps(self.model_dump()))
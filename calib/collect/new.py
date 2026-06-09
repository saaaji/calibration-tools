import typer
import tomlkit
import logging
from pathlib import Path
from ..common.camera.core.config import CameraArrayConfig
from ..common.target.core.config import TargetConfig
from ..common.archive import ArchiveManifest

app = typer.Typer(no_args_is_help=True)

@app.callback(invoke_without_command=True)
def main(
    rig: Path = typer.Option(..., "--rig", "-r", help="path to camera rig file (TOML)"),
    target: Path = typer.Option(..., "--target", "-t", help="path to target file (TOML)"),
    archive_dir: Path = typer.Option(..., "--archive-dir", "-a", envvar="COLLECT_ARCHIVE_DIR"),
    extrinsics: bool = typer.Option(False, "--ext", "-e", help="joint capture for extrinsics solve"),
    name: str = typer.Option(None, help="human readable name"),
    port: int = typer.Option(8080, help="port for capture server"),
) -> None:
    log = logging.getLogger(__name__)

    # paths to resources must exist
    assert rig.exists() and rig.is_file()
    assert target.exists() and target.is_file()
    assert archive_dir.exists() and archive_dir.is_dir()
    
    # parse configs
    rig_dict = tomlkit.parse(rig.read_text())
    rig_config = CameraArrayConfig.model_validate(rig_dict)

    for raw_cfg, cam_cfg in zip(rig_dict["cameras"], rig_config.cameras):
        print(raw_cfg.trivia)

    target_dict = tomlkit.parse(target.read_text())
    target_config = TargetConfig.model_validate(target_dict)

    # create objects
    # manifest = 
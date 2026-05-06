import typer
from pathlib import Path

app = typer.Typer(no_args_is_help=True)

@app.callback(invoke_without_command=True)
def new(
    rig: Path = typer.Option(..., help="path to camera rig file (TOML)"),
    target: Path = typer.Option(None, help="path to target file (TOML)"),
    archive_dir: Path = typer.Option(..., envvar="COLLECT_ARCHIVE_DIR"),
    extrinsic: bool = typer.Option(False, "--ext", help="joint capture for extrinsic solve"),
    name: str = typer.Option(None, help="human readable name"),
    port: int = typer.Option(8080),
) -> None:
    # paths must exist
    assert rig.exists()
    
    # parse configs
    # rig_config = 
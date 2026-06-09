import typer
import logging
from rich.logging import RichHandler
from .collect.main import app as collect_app

app = typer.Typer(name="calib", no_args_is_help=True)
app.add_typer(collect_app, name="collect")

@app.callback()
def callback(
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        handlers=[RichHandler()],
    )

def main() -> None:
    app()
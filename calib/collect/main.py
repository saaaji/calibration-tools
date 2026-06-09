import typer
from . import new

app = typer.Typer(name="collect", no_args_is_help=True)
app.add_typer(new.app, name="new")
import typer
from src.collect import new

app = typer.Typer(name="collect", no_args_is_help=True)
app.add_typer(new.app, name="new")

def main():
    print("test")
    app()

if __name__ == "__main__":
    main()
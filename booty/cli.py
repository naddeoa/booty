import click
import pathlib
import sys

from booty.app import App


@click.command()
@click.option("-c", "--config", type=str, required=False, help="Path to the install.sysc file", default="./install.booty")
@click.option("-s", "--status", type=bool, is_flag=True, required=False, help="Check the status of all known targets")
@click.option("-i", "--install", type=bool, is_flag=True, required=False, help="Install all uninstalled targets")
@click.option("-y", "--yes", type=bool, is_flag=True, required=False, help="Don't prompt for confirmation")
def cli(config: str, yes: bool, status: bool = True, install: bool = False):
    # Make sure config exists
    if not pathlib.Path(config).exists():
        click.echo(f"Config file {config} does not exist. Use -c to specify the location of an install.booty file.")
        sys.exit(1)

    if not install and not status:
        install = True

    app = App(config)
    if install:
        status_result = app.status()
        if status_result.errors:
            # Don't consider status error sufficient to stop the install attempt, sometimes is_status
            # depends on having previous things installed to work correctly
            pass

        if status_result.missing:
            if not yes:
                click.confirm("Install all missing targets?", abort=True)
            install_result = app.install_missing(status_result)
            if install_result.errors:
                # Don't consider `missing` to be an error. Some status checks may require logging in/out.
                click.echo("There were errors. See above.")
                sys.exit(1)

    elif status:
        if app.status().errors:
            click.echo("There were errors. See above.")
            sys.exit(1)


if __name__ == "__main__":
    cli()

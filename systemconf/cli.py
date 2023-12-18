import click

from systemconf.app import App


@click.command()
@click.option("-c", "--config", type=str, required=True, help="Path to the install.sysc file")
@click.option("-s", "--status", type=bool, is_flag=True, required=False, help="Check the status of all known targets")
@click.option("-i", "--install", type=bool, is_flag=True, required=False, help="Install all uninstalled targets")
def cli(config: str, status: bool = True, install: bool = False):
    app = App(config)

    has_errors = False
    if install:
        status_result = app.status()
        if status_result.errors:
            has_errors = True

        if status_result.missing:
            click.confirm("Install all missing targets?", abort=True)
            app.install_missing(status_result)
    elif status:
        if app.status().errors:
            has_errors = True

    if has_errors:
        click.echo("There were errors. See above.")
        exit(1)


if __name__ == "__main__":
    cli()

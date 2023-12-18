import click

from systemconf.app import App


@click.command()
@click.option("-c", "--config", type=str, required=True, help="Path to the install.sysc file")
@click.option("-s", "--status", type=bool, is_flag=True, required=False, help="Check the status of all known targets")
@click.option("-i", "--install", type=bool, is_flag=True, required=False, help="Install all uninstalled targets")
def cli(config: str, status: bool = True, install: bool = False):
    app = App(config)

    if install:
        status_result = app.status()
        if not status_result.missing:
            return

        click.confirm("Install all missing targets?", abort=True)
        app.install_missing(status_result)
        return

    if status:
        app.status()
        return


if __name__ == "__main__":
    cli()

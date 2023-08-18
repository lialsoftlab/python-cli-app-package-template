import click
import logging

from your_cli_app.pidfile import PidFileContext


logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", default=False, is_flag=True)
@click.pass_context
def cli(ctx, verbose):
    ctx.obj = dict(verbose_mode=verbose)


@cli.command()
@click.option("--name", default='Joe', help="Name for greeting")
@click.pass_obj
def hello(config, name):
    """Sample command"""
    with PidFileContext() as _pid:
        if config["verbose_mode"]:
            click.echo(f"You specified name '{name}'")
        click.echo(f"Hello, {name}!")







import click

from minikts.templates.template_management import init_template, TEMPLATES

@click.group()
def cli():
    pass


@cli.command()
@click.argument('name', type=click.Choice(TEMPLATES), nargs=1)
def template(name):
    init_template(name)

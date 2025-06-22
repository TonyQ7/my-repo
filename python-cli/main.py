import click

@click.group()
def cli():
    """Example CLI Utility"""

@cli.command()
@click.argument('name')
def greet(name):
    """Greet a user by name."""
    click.echo(f'Hello, {name}!')

if __name__ == '__main__':
    cli()

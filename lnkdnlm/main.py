
import sys
import click


@click.command()
def main(args=None) -> int:
    click.echo("Replace this message by putting your code into "
               "lnkdnlm.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

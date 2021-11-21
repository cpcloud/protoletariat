#!/usr/bin/env python3

from pathlib import Path

import click


@click.command()
@click.argument(
    "proto_package_dir",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True,
        path_type=Path,
    ),
)
@click.option("--overwrite/--no-overwrite", help="Overwrite all refactored files")
def main(proto_package_dir: Path, overwrite: bool) -> None:
    pass


if __name__ == "__main__":
    main()

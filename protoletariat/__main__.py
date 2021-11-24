#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Callable

import click

from .fdsetgen import Buf, Protoc


def _overwrite(python_file: Path, code: str) -> None:
    python_file.write_text(code)


def _echo(_: Path, code: str) -> None:
    click.echo(code)


def _make_callback(overwrite: bool) -> Callable[[Path, str], None]:
    return _overwrite if overwrite else _echo


@click.group(
    help="Rewrite protoc or buf-generated imports for use by the protoletariat.",
    context_settings=dict(max_content_width=88),
)
@click.option(
    "-g",
    "--generated-python-dir",
    required=True,
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True,
        path_type=Path,
    ),
    help="Directory containing generated Python code",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    help="Overwrite all relevant files under `generated_python_dir`",
    show_default=True,
)
@click.option(
    "--create-init/--dont-create-init",
    default=False,
    help="Create an empty __init__.py file under `generated_python_dir`",
    show_default=True,
)
@click.pass_context
def main(
    ctx: click.Context,
    generated_python_dir: Path,
    overwrite: bool,
    create_init: bool,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj.update(
        dict(
            generated_python_dir=generated_python_dir,
            overwrite_callback=_make_callback(overwrite),
            create_init=create_init,
        )
    )


@main.command(help="Use protoc to generate the FileDescriptorSet blob")
@click.option(
    "-p",
    "--proto-path",
    multiple=True,
    required=True,
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True,
        path_type=Path,
    ),
    help="Protobuf file search path(s). Accepts multiple values.",
)
@click.argument(
    "proto_files",
    nargs=-1,
    required=True,
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        exists=True,
        path_type=Path,
    ),
)
@click.option(
    "--protoc-path",
    envvar="PROTOC_PATH",
    type=str,
    default="protoc",
    show_default=True,
    show_envvar=True,
    help="Path to the `protoc` executable",
)
@click.pass_context
def protoc(
    ctx: click.Context,
    proto_path: list[Path],
    proto_files: list[Path],
    protoc_path: str,
) -> None:
    Protoc(protoc_path, proto_files, proto_path).fix_imports(**ctx.obj)


@main.command(help="Use buf to generate the FileDescriptorSet blob")
@click.option(
    "--buf-path",
    envvar="BUF_PATH",
    type=str,
    default="buf",
    show_default=True,
    show_envvar=True,
    help="Path to the `buf` executable",
)
@click.pass_context
def buf(ctx: click.Context, buf_path: str) -> None:
    Buf(buf_path).fix_imports(**ctx.obj)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

import click

from .fdsetgen import Buf, Protoc


def _overwrite(python_file: Path, code: str) -> None:
    python_file.write_text(code)


def _echo(_: Path, code: str) -> None:
    click.echo(code)


@click.group(
    help="Rewrite protoc or buf-generated imports for use by the protoletariat.",
    context_settings=dict(max_content_width=140),
)
@click.option(
    "-o",
    "--python-out",
    required=True,
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True,
        path_type=Path,
    ),
    help="Directory containing protoc or buf-generated Python code",
)
@click.option(
    "--in-place/--not-in-place",
    default=False,
    help="Overwrite all relevant files under `--python-out` with adjusted imports",
    show_default=True,
)
@click.option(
    "--create-package/--dont-create-package",
    default=False,
    help="Recursively create __init__.py files under `--python-out`",
    show_default=True,
)
@click.option(
    "-s",
    "--module-suffixes",
    type=str,
    multiple=True,
    default=["_pb2.py", "_pb2.pyi", "_pb2_grpc.py", "_pb2_grpc.pyi"],
    help="Suffixes of Python/mypy modules to process",
    show_default=True,
)
@click.pass_context
def main(
    ctx: click.Context,
    python_out: Path,
    in_place: bool,
    create_package: bool,
    module_suffixes: list[str],
) -> None:
    ctx.ensure_object(dict)
    ctx.obj.update(
        dict(
            python_out=python_out,
            create_package=create_package,
            overwrite_callback=_overwrite if in_place else _echo,
            module_suffixes=module_suffixes,
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

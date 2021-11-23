#!/usr/bin/env python3

from __future__ import annotations

import ast
import itertools
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

import astor
import click
from google.protobuf.descriptor_pb2 import FileDescriptorSet

from .rewrite import ImportRewriter, build_import_rewrite, register_import_rewrite


def get_file_descriptor_set(
    paths: Iterable[Path],
    proto_paths: Iterable[Path],
) -> FileDescriptorSet:
    """Parse the proto files in `paths` into a `FileDescriptorSet`."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        subprocess.check_output(
            [
                "protoc",
                "--include_imports",
                "--descriptor_set_out",
                f"{f.name}",
                *itertools.chain.from_iterable(
                    [
                        "--proto_path",
                        str(proto_path),
                    ]
                    for proto_path in proto_paths
                ),
                *map(str, paths),
            ]
        )
    try:
        return FileDescriptorSet.FromString(Path(f.name).read_bytes())
    finally:
        os.remove(f.name)


@click.command(help="Rewrite protoc-generated imports for use by the proletariat.")
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
)
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
    "--overwrite/--no-overwrite",
    default=False,
    help="Overwrite all generated Python files with modified imports",
)
@click.option(
    "--create-init/--dont-create-init",
    default=False,
    help="Create an __init__.py file under the `generated_python-dir` directory",
)
def main(
    generated_python_dir: Path,
    proto_path: list[Path],
    overwrite: bool,
    proto_files: list[Path],
    create_init: bool,
) -> None:
    fdset = get_file_descriptor_set(proto_files, proto_path)
    proto_suffix_pattern = re.compile(r"\.proto$")

    for fd in fdset.file:
        for dep in fd.dependency:
            register_import_rewrite(
                build_import_rewrite(proto_suffix_pattern.sub("", dep))
            )

    rewriter = ImportRewriter()

    # only rewrite things with dependencies
    for fd in filter(lambda fd: fd.dependency, fdset.file):
        fd_name = fd.name
        stem = proto_suffix_pattern.sub("", fd_name)
        python_file = generated_python_dir.joinpath(fd_name).with_name(f"{stem}_pb2.py")
        raw_code = python_file.read_text()
        module = ast.parse(raw_code)
        new_module = rewriter.visit(module)
        new_code = astor.to_source(new_module)
        if overwrite:
            python_file.write_text(new_code)
        else:
            click.echo(new_code)
    if create_init:
        generated_python_dir.joinpath("__init__.py").touch(exist_ok=True)


if __name__ == "__main__":
    main()

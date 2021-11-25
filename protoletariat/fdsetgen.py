from __future__ import annotations

import abc
import ast
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Iterable, Sequence

import astor
from google.protobuf.descriptor_pb2 import FileDescriptorSet

from .rewrite import ImportRewriter, build_import_rewrite, register_import_rewrite

_PROTO_SUFFIX_PATTERN = re.compile(r"^(.+)\.proto$")


class FileDescriptorSetGenerator(abc.ABC):
    def __init__(self, fdset_generator_binary: str) -> None:
        self.fdset_generator_binary = fdset_generator_binary

    @abc.abstractmethod
    def generate_file_descriptor_set_bytes(self) -> bytes:
        """Generate the bytes of a `FileDescriptorSet`"""

    def fix_imports(
        self,
        python_out: Path,
        create_package: bool,
        overwrite_callback: Callable[[Path, str], None],
        module_suffixes: Sequence[str],
    ) -> None:
        fdset = FileDescriptorSet.FromString(self.generate_file_descriptor_set_bytes())

        for fd in fdset.file:
            fd_name = _PROTO_SUFFIX_PATTERN.sub(r"\1", fd.name)
            for dep in fd.dependency:
                register_import_rewrite(
                    build_import_rewrite(fd_name, _PROTO_SUFFIX_PATTERN.sub(r"\1", dep))
                )

        rewriter = ImportRewriter()

        # only rewrite things with dependencies
        for fd_name in (fd.name for fd in fdset.file if fd.dependency):
            for suffix in module_suffixes:
                name = _PROTO_SUFFIX_PATTERN.sub(rf"\1{suffix}", fd_name)
                python_file = python_out.joinpath(name)
                if python_file.exists():
                    raw_code = python_file.read_text()
                    module = ast.parse(raw_code)
                    new_module = rewriter.visit(module)
                    new_code = astor.to_source(new_module)
                    overwrite_callback(python_file, new_code)

        if create_package:
            python_out.joinpath("__init__.py").touch(exist_ok=True)

            # recursively create packages
            for dir_entry in python_out.rglob("*"):
                if dir_entry.is_dir():
                    dir_entry.joinpath("__init__.py").touch(exist_ok=True)


class Protoc(FileDescriptorSetGenerator):
    def __init__(
        self,
        protoc_path: str,
        paths: Iterable[Path],
        proto_paths: Iterable[Path],
    ) -> None:
        super().__init__(protoc_path)
        self.paths = list(paths)
        self.proto_paths = list(proto_paths)

    def generate_file_descriptor_set_bytes(self) -> bytes:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filename = Path(f.name)
            subprocess.check_output(
                [
                    self.fdset_generator_binary,
                    "--include_imports",
                    f"--descriptor_set_out={filename}",
                    *map("--proto_path={}".format, self.proto_paths),
                    *map(str, self.paths),
                ]
            )

        try:
            return filename.read_bytes()
        finally:
            filename.unlink()


class Buf(FileDescriptorSetGenerator):
    def generate_file_descriptor_set_bytes(self) -> bytes:
        return subprocess.check_output(
            [
                self.fdset_generator_binary,
                "build",
                "--as-file-descriptor-set",
                "--exclude-source-info",
                "--output",
                "-",
            ]
        )

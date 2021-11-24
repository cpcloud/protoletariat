from __future__ import annotations

import abc
import ast
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Iterable

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
        generated_python_dir: Path,
        create_init: bool,
        overwrite_callback: Callable[[Path, str], None],
    ) -> None:
        fdset = FileDescriptorSet.FromString(self.generate_file_descriptor_set_bytes())

        for fd in fdset.file:
            for dep in fd.dependency:
                register_import_rewrite(
                    build_import_rewrite(_PROTO_SUFFIX_PATTERN.sub(r"\1", dep))
                )

        rewriter = ImportRewriter()

        # only rewrite things with dependencies
        for fd_name in (fd.name for fd in fdset.file if fd.dependency):
            name = _PROTO_SUFFIX_PATTERN.sub(r"\1_pb2.py", fd_name)
            python_file = generated_python_dir.joinpath(name)
            raw_code = python_file.read_text()
            module = ast.parse(raw_code)
            new_module = rewriter.visit(module)
            new_code = astor.to_source(new_module)
            overwrite_callback(python_file, new_code)

        if create_init:
            generated_python_dir.joinpath("__init__.py").touch(exist_ok=True)


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
                "--output",
                "-",
            ]
        )

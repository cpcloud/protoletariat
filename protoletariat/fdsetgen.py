from __future__ import annotations

import abc
import fnmatch
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Iterable, Sequence

from google.protobuf.descriptor_pb2 import FileDescriptorSet

from .rewrite import ASTImportRewriter, build_rewrites

_PROTO_SUFFIX_PATTERN = re.compile(r"^(.+)\.proto$")


def _remove_proto_suffix(name: str) -> str:
    """Remove the `.proto` suffix from `name`.

    Examples
    --------
    >>> _remove_proto_suffix("a/b.proto")
    'a/b'
    """
    return _PROTO_SUFFIX_PATTERN.sub(r"\1", name)


def _should_ignore(fd_name: str, patterns: Sequence[str]) -> bool:
    """Return whether `fd_name` should be ignored according to `patterns`.

    Examples
    --------
    >>> fd_name = "google/protobuf/empty.proto"
    >>> pattern = "google/protobuf/*"
    >>> _should_ignore(fd_name, [pattern])
    True
    >>> fd_name = "foo/bar"
    >>> _should_ignore(fd_name, [pattern])
    False
    """
    return any(fnmatch.fnmatchcase(fd_name, pattern) for pattern in patterns)


class FileDescriptorSetGenerator(abc.ABC):
    """Base class that implements fixing imports."""

    @abc.abstractmethod
    def generate_file_descriptor_set_bytes(self) -> bytes:
        """Generate the bytes of a `FileDescriptorSet`"""

    def fix_imports(
        self,
        *,
        python_out: Path,
        create_package: bool,
        overwrite_callback: Callable[[Path, str], None],
        module_suffixes: Sequence[str],
        exclude_imports_glob: Sequence[str],
    ) -> None:
        """Fix imports from protoc/buf generated code."""
        fdset = FileDescriptorSet.FromString(self.generate_file_descriptor_set_bytes())

        for fd in fdset.file:
            if _should_ignore(fd.name, exclude_imports_glob):
                continue

            fd_name = _remove_proto_suffix(fd.name)
            rewriter = ASTImportRewriter()
            # services live outside of the corresponding generated Python
            # module, but they import it so we register a rewrite for the
            # current proto as a dependency of itself to handle the case
            # of services
            for repl in build_rewrites(fd_name, fd_name):
                rewriter.register_rewrite(repl)

            # register proto import rewrites
            for dep in map(_remove_proto_suffix, fd.dependency):
                if _should_ignore(dep, exclude_imports_glob):
                    continue

                dep_name = _remove_proto_suffix(dep)
                for repl in build_rewrites(fd_name, dep_name):
                    rewriter.register_rewrite(repl)

            for suffix in module_suffixes:
                python_file = python_out.joinpath(f"{fd_name}{suffix}")
                try:
                    raw_code = python_file.read_text()
                except FileNotFoundError:
                    pass
                else:
                    new_code = rewriter.rewrite(raw_code)
                    overwrite_callback(python_file, new_code)

        if create_package:
            python_out.joinpath("__init__.py").touch(exist_ok=True)

            # recursively create packages
            for dir_entry in python_out.rglob("*"):
                if dir_entry.is_dir():
                    dir_entry.joinpath("__init__.py").touch(exist_ok=True)


class Protoc(FileDescriptorSetGenerator):
    """Generate the FileDescriptorSet using `protoc`."""

    def __init__(
        self,
        *,
        protoc_path: str,
        proto_files: Iterable[Path],
        proto_paths: Iterable[Path],
    ) -> None:
        self.protoc_path = protoc_path
        self.proto_files = proto_files
        self.proto_paths = proto_paths

    def generate_file_descriptor_set_bytes(self) -> bytes:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filename = Path(f.name)
            subprocess.check_output(
                [
                    self.protoc_path,
                    "--include_imports",
                    f"--descriptor_set_out={filename}",
                    *map("--proto_path={}".format, self.proto_paths),
                    *map(str, self.proto_files),
                ]
            )

        try:
            return filename.read_bytes()
        finally:
            filename.unlink()


class Buf(FileDescriptorSetGenerator):
    """Generate the FileDescriptorSet using `buf`."""

    def __init__(self, *, buf_path: str) -> None:
        """Construct a `buf`-based `FileDescriptorSetGenerator`.

        Parameters
        ----------
        buf_path
            Path to buf executable
        """
        self.buf_path = buf_path

    def generate_file_descriptor_set_bytes(self) -> bytes:
        return subprocess.check_output(
            [
                self.buf_path,
                "build",
                "--as-file-descriptor-set",
                "--exclude-source-info",
                "--output",
                "-",
            ]
        )


class Raw(FileDescriptorSetGenerator):
    """Generate the FileDescriptorSet using user-provided bytes."""

    def __init__(self, fdset_bytes: bytes) -> None:
        self.fdset_bytes = fdset_bytes

    def generate_file_descriptor_set_bytes(self) -> bytes:
        return self.fdset_bytes

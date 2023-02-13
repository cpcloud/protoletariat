from __future__ import annotations

import abc
import fnmatch
import itertools
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Iterable, Sequence

from google.protobuf.descriptor_pb2 import FileDescriptorSet

from .rewrite import ASTImportRewriter, build_rewrites

_PROTO_SUFFIX_PATTERN = re.compile(r"^(.+)\.proto$")


def _clean_proto_filename(name: str) -> str:
    """Remove the `.proto` suffix from `name`.

    Examples
    --------
    >>> _clean_proto_filename("a/b.proto")
    'a/b'
    >>> _clean_proto_filename("a/b-c.proto")
    'a/b_c'
    >>> _clean_proto_filename("a/b_c.proto")
    'a/b_c'
    """
    return _PROTO_SUFFIX_PATTERN.sub(r"\1", name).replace("-", "_")


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
        """Generate the bytes of a `FileDescriptorSet`."""

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

        has_pyi = any(suffix.endswith(".pyi") for suffix in module_suffixes)
        for fd in fdset.file:
            if _should_ignore(fd.name, exclude_imports_glob):
                continue

            fd_name = _clean_proto_filename(fd.name)
            rewriter = ASTImportRewriter()
            # services live outside of the corresponding generated Python
            # module, but they import it so we register a rewrite for the
            # current proto as a dependency of itself to handle the case
            # of services
            for repl in build_rewrites(fd_name, fd_name):
                rewriter.register_rewrite(repl)

            # register proto import rewrites
            for dep in map(_clean_proto_filename, fd.dependency):
                if _should_ignore(dep, exclude_imports_glob):
                    continue

                dep_name = _clean_proto_filename(dep)
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
            # recursively create packages
            for dir_entry in itertools.chain([python_out], python_out.rglob("*")):
                if dir_entry.is_dir() and "__pycache__" not in dir_entry.parts:
                    dir_entry.joinpath("__init__.py").touch(exist_ok=True)
                    if has_pyi:
                        _create_pyi_init(dir_entry)


def _create_pyi_init(root: Path) -> None:
    # use a dictionary to preserve order while deduplicating
    lines_to_write = {
        f"from . import {path.stem}\n": None
        for path in sorted(root.glob("*"))
        if path.stem not in ("__init__", "__pycache__")
        if path.suffix == ".pyi" or path.is_dir()
    }
    path = root.joinpath("__init__.pyi")

    if not path.exists():
        path.write_text("".join(lines_to_write))
    else:
        with path.open(mode="r") as f:
            for line in f:
                lines_to_write.pop(line, None)
        with path.open(mode="a") as f:
            f.writelines(lines_to_write)


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

    def __init__(self, *, buf_path: str, input: str) -> None:
        """Construct a `buf`-based `FileDescriptorSetGenerator`.

        Parameters
        ----------
        buf_path
            Path to buf executable
        input
            The source or module to build
        """
        self.buf_path = buf_path
        self.input = input

    def generate_file_descriptor_set_bytes(self) -> bytes:
        return subprocess.check_output(
            [
                self.buf_path,
                "build",
                "--as-file-descriptor-set",
                "--exclude-source-info",
                self.input,
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

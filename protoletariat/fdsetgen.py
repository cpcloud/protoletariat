from __future__ import annotations

import abc
import fnmatch
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Iterable, Sequence

from google.protobuf.descriptor_pb2 import FileDescriptorSet

from .rewrite import ASTImportRewriter, build_rewrites


def _remove_proto_suffix(name: str) -> str:
    """Remove the `.proto` suffix from `name`."""
    return str(Path(name).with_suffix("")) if name.endswith(".proto") else name


def _should_ignore(fd_name: str, patterns: Sequence[str]) -> bool:
    """Return whether `fd_name` should be ignored according to `patterns`."""
    return any(fnmatch.fnmatchcase(fd_name, pattern) for pattern in patterns)


class FileDescriptorSetGenerator(abc.ABC):
    """Base class that implements fixing imports."""

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
        exclude_imports_glob: Sequence[str],
    ) -> None:
        """Fix imports from protoc/buf generated code."""
        rewriters = {}
        fdset = FileDescriptorSet.FromString(self.generate_file_descriptor_set_bytes())

        for fd in fdset.file:
            fd_name = _remove_proto_suffix(fd.name)
            if _should_ignore(fd_name, exclude_imports_glob):
                continue
            rewriters[fd_name] = rewriter = ASTImportRewriter()
            # services live outside of the corresponding generated Python
            # module, but they import it so we register a rewrite for the
            # current proto as a dependency of itself to handle the case
            # of services
            for repl in build_rewrites(fd_name, fd_name):
                rewriter.register_rewrite(repl)

            # register _proto_ import rewrites
            for dep in fd.dependency:
                dep_name = _remove_proto_suffix(dep)
                if _should_ignore(dep_name, exclude_imports_glob):
                    continue
                for repl in build_rewrites(fd_name, dep_name):
                    rewriter.register_rewrite(repl)

        for fd in fdset.file:
            fd_name = _remove_proto_suffix(fd.name)
            for suffix in module_suffixes:
                py_name = f"{fd_name}{suffix}"
                python_file = python_out.joinpath(py_name)
                if python_file.exists():
                    raw_code = python_file.read_text()
                    try:
                        rewriter = rewriters[fd_name]
                    except KeyError:
                        # rewriters don't exist for glob-ignored names
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
    def __init__(
        self,
        protoc_path: str,
        proto_files: Iterable[Path],
        proto_paths: Iterable[Path],
    ) -> None:
        super().__init__(protoc_path)
        self.proto_files = list(proto_files)
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
                    *map(str, self.proto_files),
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

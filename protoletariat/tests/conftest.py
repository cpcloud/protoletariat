from __future__ import annotations

import abc
import contextlib
import itertools
import json
import os
import shutil
import subprocess
import tempfile
from functools import partial
from pathlib import Path
from typing import Generator, Iterable, NamedTuple, Sequence

import pytest
from _pytest.fixtures import SubRequest
from click.testing import CliRunner, Result

from protoletariat.__main__ import main


class Plugin(NamedTuple):
    name: str
    path: str | None = None


class ProtoFile(NamedTuple):
    basename: str
    code: str


class ProtoletariatFixture(abc.ABC):
    def __init__(
        self,
        *,
        base_dir: Path,
        package: str,
        proto_texts: Iterable[ProtoFile],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        assert base_dir.is_dir(), f"`{base_dir}` is not a directory"
        self.base_dir = base_dir
        self.package_dir = base_dir / package
        self.package_dir.mkdir(exist_ok=True, parents=True)
        self.proto_texts = [
            (base_dir / basename, code) for basename, code in proto_texts
        ]
        self.monkeypatch = monkeypatch

    @property
    def package_name(self) -> str:
        return self.package_dir.name

    def write_protos(self) -> None:
        for filename, code in self.proto_texts:
            filename.parent.mkdir(exist_ok=True, parents=True)
            filename.write_text(code)

    def generate(
        self,
        cli: CliRunner,
        *,
        args: Iterable[str] = (),
    ) -> Result:
        self.write_protos()
        cwd = os.getcwd()
        self.monkeypatch.chdir(self.base_dir)
        result = self.do_generate(cli, args=args)
        self.monkeypatch.chdir(cwd)
        return result

    @abc.abstractmethod
    def do_generate(self, cli: CliRunner, *, args: Iterable[str]) -> Result:
        ...

    @property  # type: ignore[misc]
    @contextlib.contextmanager
    def patched_syspath(self) -> Generator[None, None, None]:
        with self.monkeypatch.context() as m:
            m.syspath_prepend(str(self.base_dir))
            yield

    def check_proto_out(self) -> None:
        py_files = list(self.package_dir.rglob("*.py"))
        assert py_files
        assert all(path.read_text() for path in py_files)


class BufFixture(ProtoletariatFixture):
    def __init__(
        self,
        *,
        base_dir: Path,
        package: str,
        proto_texts: Iterable[ProtoFile],
        plugins: Sequence[Plugin] = (Plugin(name="python"),),
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        super().__init__(
            base_dir=base_dir,
            package=package,
            proto_texts=proto_texts,
            monkeypatch=monkeypatch,
        )

        self.base_dir.joinpath("buf.yaml").write_text(
            json.dumps(
                {
                    "version": "v1",
                    "lint": {"use": ["DEFAULT"]},
                    "breaking": {"use": ["FILE"]},
                },
            )
        )

        plugin_specs = []
        for plugin in plugins:
            plugin_spec = {"name": plugin.name, "out": str(self.package_dir)}
            if plugin.path is not None:
                plugin_spec["path"] = str(plugin.path)
            plugin_specs.append(plugin_spec)

        self.base_dir.joinpath("buf.gen.yaml").write_text(
            json.dumps({"version": "v1", "plugins": plugin_specs})
        )

    def do_generate(self, cli: CliRunner, *, args: Iterable[str] = ()) -> Result:
        try:
            subprocess.check_call(["buf", "generate"], cwd=str(self.base_dir))
        except FileNotFoundError:
            pytest.skip("buf executable not found")
        else:
            return cli.invoke(
                main,
                ["--python-out", str(self.package_dir), *args, "buf", os.getcwd()],
                catch_exceptions=False,
            )


class ProtocFixture(ProtoletariatFixture):
    def __init__(
        self,
        *,
        base_dir: Path,
        package: str,
        proto_texts: Iterable[ProtoFile],
        monkeypatch: pytest.MonkeyPatch,
        grpc: bool = False,
        mypy: bool = False,
        mypy_grpc: bool = False,
    ) -> None:
        super().__init__(
            base_dir=base_dir,
            package=package,
            proto_texts=proto_texts,
            monkeypatch=monkeypatch,
        )
        self.grpc = grpc
        self.mypy = mypy
        self.mypy_grpc = mypy_grpc

    def do_generate(self, cli: CliRunner, *, args: Iterable[str] = ()) -> Result:
        protoc_args = [
            "protoc",
            "--proto_path",
            str(self.base_dir),
            "--python_out",
            str(self.package_dir),
            *(str(filename) for filename, _ in self.proto_texts),
        ]
        if self.grpc:
            # XXX: why isn't this found? PATH is set properly
            grpc_python_plugin = shutil.which("grpc_python_plugin")
            protoc_args.extend(
                (
                    f"--plugin=protoc-gen-grpc_python={grpc_python_plugin}",
                    "--grpc_python_out",
                    str(self.package_dir),
                )
            )
        if self.mypy:
            protoc_args.extend(("--mypy_out", str(self.package_dir)))
        if self.mypy_grpc:
            protoc_args.extend(("--mypy_grpc_out", str(self.package_dir)))
        subprocess.check_call(protoc_args)
        return cli.invoke(
            main,
            [
                "--python-out",
                str(self.package_dir),
                *args,
                "protoc",
                "--proto-path",
                str(self.base_dir),
                *(str(filename) for filename, _ in self.proto_texts),
            ],
            catch_exceptions=False,
        )


class RawFixture(ProtoletariatFixture):
    def __init__(
        self,
        *,
        base_dir: Path,
        package: str,
        proto_texts: Iterable[ProtoFile],
        monkeypatch: pytest.MonkeyPatch,
        grpc: bool = False,
        mypy: bool = False,
        mypy_grpc: bool = False,
    ) -> None:
        super().__init__(
            base_dir=base_dir,
            package=package,
            proto_texts=proto_texts,
            monkeypatch=monkeypatch,
        )
        self.grpc = grpc
        self.mypy = mypy
        self.mypy_grpc = mypy_grpc

    def do_generate(self, cli: CliRunner, *, args: Iterable[str] = ()) -> Result:
        # TODO: refactor this, it duplicates a lot of what's in ProtocFixture
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filename = f.name

            protoc_args = [
                "protoc",
                "--include_imports",
                f"--descriptor_set_out={filename}",
                "--proto_path",
                str(self.base_dir),
                "--python_out",
                str(self.package_dir),
                *(str(fn) for fn, _ in self.proto_texts),
            ]

            if self.grpc:
                # XXX: why isn't this found? PATH is set properly
                grpc_python_plugin = shutil.which("grpc_python_plugin")
                protoc_args.extend(
                    (
                        f"--plugin=protoc-gen-grpc_python={grpc_python_plugin}",
                        "--grpc_python_out",
                        str(self.package_dir),
                    )
                )
            if self.mypy:
                protoc_args.extend(("--mypy_out", str(self.package_dir)))
            if self.mypy_grpc:
                protoc_args.extend(("--mypy_grpc_out", str(self.package_dir)))

            subprocess.check_call(protoc_args)

        protol_args = ["--python-out", str(self.package_dir), *args, "raw", filename]

        try:
            return cli.invoke(main, protol_args, catch_exceptions=False)
        finally:
            os.unlink(filename)


@pytest.fixture
def cli() -> CliRunner:
    return CliRunner()


@pytest.fixture(params=["_", "-"])
def basic_cli_texts(request: SubRequest) -> list[ProtoFile]:
    sep = request.param
    this_code = f"""
syntax = "proto3";

import "other.proto";
import "baz/bizz{sep}buzz.proto";

package protoletariat.test;

message Test {{
    Other test = 1;
    protoletariat.test.baz.BuzzBuzz baz = 2;
}}"""
    other_code = """
syntax = "proto3";

package protoletariat.test;

message Other {}
"""
    baz_bizz_buzz_code = """
syntax = "proto3";

package protoletariat.test.baz;

message BuzzBuzz {}
"""
    return [
        ProtoFile(basename="this.proto", code=this_code),
        ProtoFile(basename="other.proto", code=other_code),
        ProtoFile(
            basename=f"baz/bizz{sep}buzz.proto",
            code=baz_bizz_buzz_code,
        ),
    ]


@pytest.fixture(
    params=[
        pytest.param(
            partial(
                BufFixture,
                plugins=[Plugin(name="python")],
                package="basic_cli",
            ),
            id="basic_cli_buf",
        ),
        pytest.param(
            partial(ProtocFixture, package="basic_cli"),
            id="basic_cli_protoc",
        ),
        pytest.param(
            partial(RawFixture, package="basic_cli"),
            id="basic_cli_raw",
        ),
    ]
)
def basic_cli(
    request: SubRequest,
    tmp_path: Path,
    basic_cli_texts: list[ProtoFile],
    monkeypatch: pytest.MonkeyPatch,
) -> ProtoletariatFixture:
    return request.param(
        base_dir=tmp_path,
        proto_texts=basic_cli_texts,
        monkeypatch=monkeypatch,
    )


@pytest.fixture(params=["_", "-"])
def thing_service_texts(request: SubRequest) -> list[ProtoFile]:
    sep = request.param
    thing_service_code = """
syntax = "proto3";

import "thing1.proto";
import "thing2.proto";

package things;

service ThingService {
    rpc GetThing1(Thing1) returns (Thing1) {}
    rpc GetThing2(Thing2) returns (Thing2) {}
}
"""
    thing1_code = """
syntax = "proto3";

import "thing2.proto";

package things;

message Thing1 {
  Thing2 thing2 = 1;
}
"""
    thing2_code = """
syntax = "proto3";

package things;

message Thing2 {
  string data = 1;
}
"""
    return [
        ProtoFile(basename=f"thing{sep}service.proto", code=thing_service_code),
        ProtoFile(basename="thing1.proto", code=thing1_code),
        ProtoFile(basename="thing2.proto", code=thing2_code),
    ]


@pytest.fixture(
    params=[
        pytest.param(
            partial(
                BufFixture,
                plugins=[
                    Plugin(name="python"),
                    Plugin(name="grpc_python", path="grpc_python_plugin"),
                ],
                package="thing_service",
            ),
            id="thing_service_buf",
        ),
        pytest.param(
            partial(ProtocFixture, package="thing_service", grpc=True),
            id="thing_service_protoc",
        ),
        pytest.param(
            partial(RawFixture, package="thing_service", grpc=True),
            id="thing_service_raw",
        ),
    ]
)
def thing_service(
    request: SubRequest,
    tmp_path: Path,
    thing_service_texts: list[ProtoFile],
    monkeypatch: pytest.MonkeyPatch,
) -> ProtoletariatFixture:
    return request.param(
        base_dir=tmp_path,
        proto_texts=thing_service_texts,
        monkeypatch=monkeypatch,
    )


@pytest.fixture
def nested_texts() -> list[ProtoFile]:
    thing1_code = """
syntax = "proto3";

import "a/b/c/thing2.proto";

package thing1.a;

message Thing1 {
  thing2.a.b.c.Thing2 thing2 = 1;
}
"""

    thing2_code = """
syntax = "proto3";

package thing2.a.b.c;

message Thing2 {
  string data = 1;
}
"""
    return [
        ProtoFile(basename="d/thing1.proto", code=thing1_code),
        ProtoFile(basename="a/b/c/thing2.proto", code=thing2_code),
    ]


@pytest.fixture(
    params=[
        pytest.param(
            partial(BufFixture, plugins=[Plugin(name="python")], package="nested"),
            id="nested_buf",
        ),
        pytest.param(partial(ProtocFixture, package="nested"), id="nested_protoc"),
        pytest.param(partial(RawFixture, package="nested"), id="nested_raw"),
    ]
)
def nested(
    request: SubRequest,
    tmp_path: Path,
    nested_texts: list[ProtoFile],
    monkeypatch: pytest.MonkeyPatch,
) -> ProtoletariatFixture:
    return request.param(
        base_dir=tmp_path,
        proto_texts=nested_texts,
        monkeypatch=monkeypatch,
    )


@pytest.fixture(params=itertools.product("_-", repeat=2))
def no_imports_service_texts(request: SubRequest) -> list[ProtoFile]:
    sep1, sep2 = request.param
    code = """
syntax = "proto3";

package no_imports.a.b;

message Request {}
message Response {}

service NoImportsService {
    rpc Get(Request) returns (Response) {}
}
"""
    return [ProtoFile(basename=f"no{sep1}imports{sep2}service.proto", code=code)]


@pytest.fixture(
    params=[
        pytest.param(
            partial(
                BufFixture,
                plugins=[
                    Plugin(name="python"),
                    Plugin(name="grpc_python", path="grpc_python_plugin"),
                    Plugin(name="mypy"),
                    Plugin(name="mypy_grpc"),
                ],
                package="no_imports_service",
            ),
            id="no_imports_service_buf",
        ),
        pytest.param(
            partial(
                ProtocFixture,
                package="no_imports_service",
                grpc=True,
                mypy=True,
                mypy_grpc=True,
            ),
            id="no_imports_service_protoc",
        ),
        pytest.param(
            partial(
                RawFixture,
                package="no_imports_service",
                grpc=True,
                mypy=True,
                mypy_grpc=True,
            ),
            id="no_imports_service_raw",
        ),
    ]
)
def no_imports_service(
    request: SubRequest,
    tmp_path: Path,
    no_imports_service_texts: list[ProtoFile],
    monkeypatch: pytest.MonkeyPatch,
) -> ProtoletariatFixture:
    return request.param(
        base_dir=tmp_path,
        proto_texts=no_imports_service_texts,
        monkeypatch=monkeypatch,
    )


@pytest.fixture(params=["_", "-"])
def imports_service_texts(request: SubRequest) -> list[ProtoFile]:
    sep = request.param
    imports_code = """
syntax = "proto3";

import "requests/get.proto";
import "requests/post.proto";

package imports_service;

service ImportsService {
    rpc Get(msg.GetRequest) returns (msg.GetResponse) {}
    rpc Post(msg.PostRequest) returns (msg.PostResponse) {}
}
"""
    requests_get_code = """
syntax = "proto3";

package imports_service.msg;

message GetRequest {}
message GetResponse {}
"""
    requests_post_code = """
syntax = "proto3";

package imports_service.msg;

message PostRequest {}
message PostResponse {}
"""
    return [
        ProtoFile(basename=f"imports{sep}service.proto", code=imports_code),
        ProtoFile(basename="requests/get.proto", code=requests_get_code),
        ProtoFile(basename="requests/post.proto", code=requests_post_code),
    ]


@pytest.fixture(
    params=[
        pytest.param(
            partial(
                BufFixture,
                plugins=[
                    Plugin(name="python"),
                    Plugin(name="grpc_python", path="grpc_python_plugin"),
                    Plugin(name="mypy"),
                    Plugin(name="mypy_grpc"),
                ],
                package="imports_service",
            ),
            id="imports_service_buf",
        ),
        pytest.param(
            partial(
                ProtocFixture,
                package="imports_service",
                grpc=True,
                mypy=True,
                mypy_grpc=True,
            ),
            id="imports_service_protoc",
        ),
        pytest.param(
            partial(
                RawFixture,
                package="imports_service",
                grpc=True,
                mypy=True,
                mypy_grpc=True,
            ),
            id="imports_service_raw",
        ),
    ]
)
def grpc_imports(
    request: SubRequest,
    tmp_path: Path,
    imports_service_texts: list[ProtoFile],
    monkeypatch: pytest.MonkeyPatch,
) -> ProtoletariatFixture:
    return request.param(
        base_dir=tmp_path,
        proto_texts=imports_service_texts,
        monkeypatch=monkeypatch,
    )


@pytest.fixture
def long_names_texts() -> list[ProtoFile]:
    # taken from https://github.com/substrait-io/substrait
    code = """
syntax = "proto3";

package io.substrait;

message FunctionSignature {
    message FinalArgVariadic {
        int64 min_args = 1;
        int64 max_args = 2;
        ParameterConsistency consistency = 3;
        enum ParameterConsistency {
            UNKNOWN = 0;
            CONSISTENT = 1;
            INCONSISTENT = 2;
        }
    }
}"""
    return [ProtoFile(basename="function.proto", code=code)]


@pytest.fixture(
    params=[
        pytest.param(
            partial(BufFixture, plugins=[Plugin(name="mypy")], package="long_names"),
            id="long_names_buf",
        ),
        pytest.param(
            partial(ProtocFixture, package="long_names", mypy=True),
            id="long_names_protoc",
        ),
        pytest.param(
            partial(RawFixture, package="long_names", mypy=True),
            id="long_names_raw",
        ),
    ]
)
def long_names(
    request: SubRequest,
    tmp_path: Path,
    long_names_texts: list[ProtoFile],
    monkeypatch: pytest.MonkeyPatch,
) -> ProtoletariatFixture:
    return request.param(
        base_dir=tmp_path,
        proto_texts=long_names_texts,
        monkeypatch=monkeypatch,
    )


@pytest.fixture(params=["_", "-"])
def ignored_import_texts(request: SubRequest) -> list[ProtoFile]:
    sep = request.param
    ignored_import_code = """
syntax = "proto3";

import "google/protobuf/empty.proto";
import "ignored.proto";

message Foo {}
"""
    ignored_code = ""
    return [
        ProtoFile(basename=f"ignored{sep}import.proto", code=ignored_import_code),
        ProtoFile(basename="ignored.proto", code=ignored_code),
    ]


@pytest.fixture(
    params=[
        pytest.param(
            partial(
                BufFixture,
                plugins=[Plugin(name="python")],
                package="ignored_imports",
            ),
            id="ignored_imports_buf",
        ),
        pytest.param(
            partial(ProtocFixture, package="ignored_imports"),
            id="ignored_imports_protoc",
        ),
        pytest.param(
            partial(RawFixture, package="ignored_imports"),
            id="ignored_imports_raw",
        ),
    ]
)
def ignored_imports(
    request: SubRequest,
    tmp_path: Path,
    ignored_import_texts: list[ProtoFile],
    monkeypatch: pytest.MonkeyPatch,
) -> ProtoletariatFixture:
    return request.param(
        base_dir=tmp_path,
        proto_texts=ignored_import_texts,
        monkeypatch=monkeypatch,
    )


def check_import_lines(result: Result, expected_lines: Iterable[str]) -> None:
    lines = result.stdout.splitlines()
    assert set(expected_lines) <= set(lines)

import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import pytest
from click.testing import CliRunner, Result

from protoletariat.__main__ import main
from protoletariat.rewrite import build_import_rewrite


def check_import_lines(result: Result, expected_lines: Iterable[str]) -> None:
    lines = result.stdout.splitlines()
    assert set(expected_lines) <= set(lines)


def check_proto_out(out: Path) -> None:
    assert list(out.rglob("*.py"))
    assert all(path.read_text() for path in out.rglob("*.py"))


@pytest.mark.parametrize(
    ("proto", "dep", "expected"),
    [
        ("a", "foo", "from . import foo_pb2 as foo__pb2"),
        ("a/b", "foo", "from .. import foo_pb2 as foo__pb2"),
        ("a", "foo/bar", "from .foo import bar_pb2 as foo_dot_bar__pb2"),
        ("a/b", "foo/bar", "from ..foo import bar_pb2 as foo_dot_bar__pb2"),
        (
            "a",
            "foo/bar/baz",
            "from .foo.bar import baz_pb2 as foo_dot_bar_dot_baz__pb2",
        ),
        (
            "a/b",
            "foo/bar/baz",
            "from ..foo.bar import baz_pb2 as foo_dot_bar_dot_baz__pb2",
        ),
        (
            "a",
            "foo/bar/bizz_buzz",
            "from .foo.bar import bizz_buzz_pb2 as foo_dot_bar_dot_bizz__buzz__pb2",
        ),
        (
            "a/b",
            "foo/bar/bizz_buzz",
            "from ..foo.bar import bizz_buzz_pb2 as foo_dot_bar_dot_bizz__buzz__pb2",
        ),
    ],
)
def test_build_import_rewrite(proto: str, dep: str, expected: str) -> None:
    old, new = build_import_rewrite(proto, dep)
    assert new == expected


@pytest.fixture
def cli() -> CliRunner:
    return CliRunner()


@pytest.fixture
def this_proto(tmp_path: Path) -> Path:
    code = """
syntax = "proto3";

import "other.proto";
import "baz/bizz_buzz.proto";

package protoletariat.test;

message Test {
    Other test = 1;
    protoletariat.test.baz.BuzzBuzz baz = 2;
}
"""
    p = tmp_path.joinpath("this.proto")
    p.write_text(code)
    return p


@pytest.fixture
def other_proto(tmp_path: Path) -> Path:
    code = """
syntax = "proto3";

package protoletariat.test;

message Other {}
"""
    p = tmp_path.joinpath("other.proto")
    p.write_text(code)
    return p


@pytest.fixture
def baz_bizz_buzz_other_proto(tmp_path: Path) -> Path:
    code = """
syntax = "proto3";

package protoletariat.test.baz;

message BuzzBuzz {}
"""
    baz = tmp_path.joinpath("baz")
    baz.mkdir()
    p = baz.joinpath("bizz_buzz.proto")
    p.write_text(code)
    return p


def test_cli(
    cli: CliRunner,
    tmp_path: Path,
    this_proto: Path,
    other_proto: Path,
    baz_bizz_buzz_other_proto: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 1. generated code using protoc
    out = tmp_path.joinpath("out_cli")
    out.mkdir()
    subprocess.run(
        [
            "protoc",
            str(this_proto),
            str(other_proto),
            str(baz_bizz_buzz_other_proto),
            "--proto_path",
            str(this_proto.parent),
            "--proto_path",
            str(other_proto.parent),
            "--proto_path",
            str(baz_bizz_buzz_other_proto),
            "--python_out",
            str(out),
        ]
    )

    check_proto_out(out)

    result = cli.invoke(
        main,
        [
            "-g",
            str(out),
            "--no-overwrite",
            "protoc",
            "-p",
            str(this_proto.parent),
            "-p",
            str(other_proto.parent),
            "-p",
            str(baz_bizz_buzz_other_proto.parent),
            str(this_proto),
            str(other_proto),
            str(baz_bizz_buzz_other_proto),
        ],
    )
    assert result.exit_code == 0

    expected_lines = [
        "from . import other_pb2 as other__pb2",
        "from .baz import bizz_buzz_pb2 as baz_dot_bizz__buzz__pb2",
    ]

    check_import_lines(result, expected_lines)

    result = cli.invoke(
        main,
        [
            "-g",
            str(out),
            "--overwrite",
            "--create-init",
            "protoc",
            "-p",
            str(this_proto.parent),
            "-p",
            str(other_proto.parent),
            "-p",
            str(baz_bizz_buzz_other_proto.parent),
            str(this_proto),
            str(other_proto),
            str(baz_bizz_buzz_other_proto),
        ],
    )
    assert result.exit_code == 0

    with monkeypatch.context() as m:
        m.syspath_prepend(str(tmp_path))
        importlib.import_module("out_cli")
        importlib.import_module("out_cli.other_pb2")
        importlib.import_module("out_cli.this_pb2")

    assert str(tmp_path) not in sys.path


@pytest.fixture
def thing1_text() -> str:
    return """
// thing1.proto
syntax = "proto3";

import "thing2.proto";

package things;

message Thing1 {
  Thing2 thing2 = 1;
}
"""


@pytest.fixture
def thing1(thing1_text: str, tmp_path: Path) -> Path:
    p = tmp_path.joinpath("thing1.proto")
    p.write_text(thing1_text)
    return p


@pytest.fixture
def thing2_text() -> str:
    return """
// thing2.proto
syntax = "proto3";

package things;

message Thing2 {
  string data = 1;
}
"""


@pytest.fixture
def thing2(thing2_text: str, tmp_path: Path) -> Path:
    code = """
// thing2.proto
syntax = "proto3";

package things;

message Thing2 {
  string data = 1;
}
"""
    p = tmp_path.joinpath("thing2.proto")
    p.write_text(code)
    return p


@pytest.fixture
def thing1_nested_text() -> str:
    return """
// thing1.proto
syntax = "proto3";

import "a/b/c/thing2.proto";

package thing1.a;

message Thing1 {
  thing2.a.b.c.Thing2 thing2 = 1;
}
"""


@pytest.fixture
def thing2_nested_text() -> str:
    return """
// thing2.proto
syntax = "proto3";

package thing2.a.b.c;

message Thing2 {
  string data = 1;
}
"""


def test_example_protoc(
    cli: CliRunner,
    tmp_path: Path,
    thing1: Path,
    thing2: Path,
) -> None:
    out = tmp_path.joinpath("out")
    out.mkdir()
    subprocess.run(
        [
            "protoc",
            str(thing1),
            str(thing2),
            "--proto_path",
            str(thing1.parent),
            "--proto_path",
            str(thing2.parent),
            "--python_out",
            str(out),
        ]
    )

    result = cli.invoke(
        main,
        [
            "-g",
            str(out),
            "--no-overwrite",
            "--create-init",
            "protoc",
            "-p",
            str(thing1.parent),
            "-p",
            str(thing2.parent),
            str(thing1),
            str(thing2),
        ],
    )
    assert result.exit_code == 0

    expected_lines = ["from . import thing2_pb2 as thing2__pb2"]
    check_import_lines(result, expected_lines)

    assert out.joinpath("__init__.py").exists()


def test_example_buf(
    cli: CliRunner,
    tmp_path: Path,
    thing1: Path,
    thing2: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path.joinpath("out")
    out.mkdir()

    monkeypatch.chdir(tmp_path)
    with tmp_path.joinpath("buf.yaml").open(mode="w") as f:
        json.dump(
            {
                "version": "v1",
                "lint": {"use": ["DEFAULT"]},
                "breaking": {"use": ["FILE"]},
            },
            f,
        )

    with tmp_path.joinpath("buf.gen.yaml").open(mode="w") as f:
        json.dump(
            {
                "version": "v1",
                "plugins": [
                    {
                        "name": "python",
                        "out": str(out),
                    }
                ],
            },
            f,
        )

    subprocess.check_call(
        [
            "protoc",
            str(thing1),
            str(thing2),
            "--proto_path",
            str(thing1.parent),
            "--proto_path",
            str(thing2.parent),
            "--python_out",
            str(out),
        ],
    )

    check_proto_out(out)

    result = cli.invoke(
        main,
        [
            "-g",
            str(out),
            "--no-overwrite",
            "--create-init",
            "buf",
        ],
    )
    assert result.exit_code == 0

    expected_lines = ["from . import thing2_pb2 as thing2__pb2"]
    check_import_lines(result, expected_lines)

    assert out.joinpath("__init__.py").exists()


def test_nested_buf(
    cli: CliRunner,
    tmp_path: Path,
    thing1_nested_text: str,
    thing2_nested_text: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path.joinpath("out_nested")
    out.mkdir()

    c = tmp_path / "a" / "b" / "c"
    c.mkdir(parents=True, exist_ok=True)

    thing2 = c / "thing2.proto"
    thing2.write_text(thing2_nested_text)

    d = tmp_path / "d"
    d.mkdir()

    thing1 = d / "thing1.proto"
    thing1.write_text(thing1_nested_text)

    monkeypatch.chdir(tmp_path)
    with tmp_path.joinpath("buf.yaml").open(mode="w") as f:
        json.dump(
            {
                "version": "v1",
                "lint": {"use": ["DEFAULT"]},
                "breaking": {"use": ["FILE"]},
            },
            f,
        )

    with tmp_path.joinpath("buf.gen.yaml").open(mode="w") as f:
        json.dump(
            {
                "version": "v1",
                "plugins": [
                    {
                        "name": "python",
                        "out": str(out),
                    },
                ],
            },
            f,
        )

    subprocess.check_call(
        [
            "protoc",
            str(thing1),
            str(thing2),
            "--proto_path",
            str(tmp_path),
            "--python_out",
            str(out),
        ],
    )

    check_proto_out(out)

    result = cli.invoke(
        main,
        [
            "-g",
            str(out),
            "--overwrite",
            "--create-init",
            "buf",
        ],
    )
    assert result.exit_code == 0

    # check that we can import nested things
    with monkeypatch.context() as m:
        m.syspath_prepend(str(tmp_path))

        importlib.import_module("out_nested")
        importlib.import_module("out_nested.a.b.c.thing2_pb2")
        importlib.import_module("out_nested.d.thing1_pb2")

    # check that we created packages in the correct locations
    assert out.joinpath("__init__.py").exists()
    assert out.joinpath("a", "__init__.py").exists()
    assert out.joinpath("a", "b", "__init__.py").exists()
    assert out.joinpath("a", "b", "c", "__init__.py").exists()
    assert out.joinpath("d", "__init__.py").exists()

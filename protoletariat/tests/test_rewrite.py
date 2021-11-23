import subprocess

import pytest
from click.testing import CliRunner

from protoletariat.__main__ import main
from protoletariat.rewrite import build_import_rewrite


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("foo", "from . import foo_pb2 as foo__pb2"),
        ("foo/bar", "from .foo import bar_pb2 as foo_dot_bar__pb2"),
        ("foo/bar/baz", "from .foo.bar import baz_pb2 as foo_dot_bar_dot_baz__pb2"),
        (
            "foo/bar/bizz_buzz",
            "from .foo.bar import bizz_buzz_pb2 as foo_dot_bar_dot_bizz__buzz__pb2",
        ),
    ],
)
def test_build_import_rewrite(case, expected):
    old, new = build_import_rewrite(case)
    assert new == expected


@pytest.fixture
def cli():
    return CliRunner()


@pytest.fixture
def this_proto(tmp_path):
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
def other_proto(tmp_path):
    code = """
syntax = "proto3";

package protoletariat.test;

message Other {}
"""
    p = tmp_path.joinpath("other.proto")
    p.write_text(code)
    return p


@pytest.fixture
def baz_bizz_buzz_other_proto(tmp_path):
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


def test_cli(cli, tmp_path, this_proto, other_proto, baz_bizz_buzz_other_proto):
    # 1. generated code using protoc
    out = tmp_path.joinpath("out")
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

    result = cli.invoke(
        main,
        [
            "-g",
            str(out),
            "-p",
            str(this_proto.parent),
            "-p",
            str(other_proto.parent),
            "-p",
            str(baz_bizz_buzz_other_proto.parent),
            str(this_proto),
            str(other_proto),
            str(baz_bizz_buzz_other_proto),
            "--no-overwrite",
        ],
    )
    assert result.exit_code == 0

    lines = result.stdout.splitlines()
    assert 'from . import other_pb2 as other__pb2' in lines
    assert 'from .baz import bizz_buzz_pb2 as baz_dot_bizz__buzz__pb2' in lines


@pytest.fixture
def thing1(tmp_path):
    code = """
// thing1.proto
syntax = "proto3";

import "thing2.proto";

package things;

message Thing1 {
  Thing2 thing2 = 1;
}
"""
    p = tmp_path.joinpath("thing1.proto")
    p.write_text(code)
    return p


@pytest.fixture
def thing2(tmp_path):
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


def test_example(cli, tmp_path, thing1, thing2):
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
            "-p",
            str(thing1.parent),
            "-p",
            str(thing2.parent),
            str(thing1),
            str(thing2),
            "--no-overwrite",
            "--create-init",
        ],
    )
    assert result.exit_code == 0

    lines = result.stdout.splitlines()
    assert 'from . import thing2_pb2 as thing2__pb2' in lines

    assert out.joinpath("__init__.py").exists()

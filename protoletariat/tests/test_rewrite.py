import importlib
import itertools
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import pytest
from click.testing import CliRunner

from protoletariat.__main__ import main
from protoletariat.rewrite import build_rewrites

from .conftest import check_import_lines, check_proto_out


@pytest.mark.parametrize(
    ("proto", "dep", "expecteds"),
    [
        pytest.param(
            "a",
            "foo",
            [
                "from . import foo_pb2 as foo__pb2",
                "from . import foo_pb2",
            ],
            id="no_nesting",
        ),
        pytest.param(
            "a/b",
            "foo",
            [
                "from .. import foo_pb2 as foo__pb2",
                "from .. import foo_pb2",
            ],
            id="proto_one_level",
        ),
        pytest.param(
            "a",
            "foo/bar",
            [
                "from .foo import bar_pb2 as foo_dot_bar__pb2",
                "from . import foo",
            ],
            id="dep_one_level",
        ),
        pytest.param(
            "a/b",
            "foo/bar",
            [
                "from ..foo import bar_pb2 as foo_dot_bar__pb2",
                "from .. import foo",
            ],
            id="both_one_level",
        ),
        pytest.param(
            "a",
            "foo/bar/baz",
            [
                "from .foo.bar import baz_pb2 as foo_dot_bar_dot_baz__pb2",
                "from . import foo",
            ],
            id="dep_two_levels",
        ),
        pytest.param(
            "a/b",
            "foo/bar/baz",
            [
                "from ..foo.bar import baz_pb2 as foo_dot_bar_dot_baz__pb2",
                "from .. import foo",
            ],
            id="proto_one_level_dep_two_levels",
        ),
        pytest.param(
            "a",
            "foo/bar/bizz_buzz",
            [
                "from .foo.bar import bizz_buzz_pb2 as foo_dot_bar_dot_bizz__buzz__pb2",
                "from . import foo",
            ],
            id="dep_three_levels",
        ),
        pytest.param(
            "a/b",
            "foo/bar/bizz_buzz",
            [
                (
                    "from ..foo.bar import bizz_buzz_pb2 as "
                    "foo_dot_bar_dot_bizz__buzz__pb2"
                ),
                "from .. import foo",
            ],
            id="proto_one_level_dep_three_levels",
        ),
        pytest.param(
            "a/b",
            "a/b",
            [
                "from ..a import b_pb2 as a_dot_b__pb2",
                "from .. import a",
            ],
            id="self_dep",
        ),
    ],
)
def test_build_import_rewrites(proto: str, dep: str, expecteds: Iterable[str]) -> None:
    rewrites = build_rewrites(proto, dep)
    for (_, new), expected in itertools.zip_longest(rewrites, expecteds):
        assert new == expected


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
            str(tmp_path),
            "--python_out",
            str(out),
        ]
    )

    check_proto_out(out)

    result = cli.invoke(
        main,
        [
            "-o",
            str(out),
            "--not-in-place",
            "protoc",
            "-p",
            str(tmp_path),
            str(this_proto),
            str(other_proto),
            str(baz_bizz_buzz_other_proto),
        ],
        catch_exceptions=False,
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
            "-o",
            str(out),
            "--in-place",
            "--create-package",
            "protoc",
            "-p",
            str(tmp_path),
            str(this_proto),
            str(other_proto),
            str(baz_bizz_buzz_other_proto),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    with monkeypatch.context() as m:
        m.syspath_prepend(str(tmp_path))
        importlib.import_module("out_cli")
        importlib.import_module("out_cli.other_pb2")
        importlib.import_module("out_cli.this_pb2")

    assert str(tmp_path) not in sys.path


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
            str(tmp_path),
            "--python_out",
            str(out),
        ],
    )

    result = cli.invoke(
        main,
        [
            "-o",
            str(out),
            "--not-in-place",
            "--create-package",
            "protoc",
            "-p",
            str(tmp_path),
            str(thing1),
            str(thing2),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    expected_lines = ["from . import thing2_pb2 as thing2__pb2"]
    check_import_lines(result, expected_lines)

    assert out.joinpath("__init__.py").exists()

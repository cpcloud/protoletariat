import importlib
import itertools
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import pytest
from click.testing import CliRunner, Result

from protoletariat.__main__ import main
from protoletariat.rewrite import build_rewrites


def check_import_lines(result: Result, expected_lines: Iterable[str]) -> None:
    lines = result.stdout.splitlines()
    assert set(expected_lines) <= set(lines)


def check_proto_out(out: Path) -> None:
    assert list(out.rglob("*.py"))
    assert all(path.read_text() for path in out.rglob("*.py"))


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


def test_example_buf(
    cli: CliRunner,
    tmp_path: Path,
    thing1: Path,
    thing2: Path,
    buf_yaml: Path,
    buf_gen_yaml: Path,
    out: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    monkeypatch.chdir(tmp_path)

    result = cli.invoke(
        main,
        [
            "-o",
            str(out),
            "--not-in-place",
            "--create-package",
            "buf",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    expected_lines = ["from . import thing2_pb2 as thing2__pb2"]
    check_import_lines(result, expected_lines)

    assert out.joinpath("__init__.py").exists()


def test_nested_buf(
    cli: CliRunner,
    tmp_path: Path,
    buf_yaml: Path,
    buf_gen_yaml_nested: Path,
    out_nested: Path,
    thing1_nested_text: str,
    thing2_nested_text: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = tmp_path / "a" / "b" / "c"
    c.mkdir(parents=True, exist_ok=True)

    thing2 = c / "thing2.proto"
    thing2.write_text(thing2_nested_text)

    d = tmp_path / "d"
    d.mkdir()

    thing1 = d / "thing1.proto"
    thing1.write_text(thing1_nested_text)

    subprocess.check_call(
        [
            "protoc",
            str(thing1),
            str(thing2),
            "--proto_path",
            str(tmp_path),
            "--python_out",
            str(out_nested),
        ],
    )

    check_proto_out(out_nested)

    monkeypatch.chdir(tmp_path)

    result = cli.invoke(
        main,
        [
            "-o",
            str(out_nested),
            "--in-place",
            "--create-package",
            "buf",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # check that we can import nested things
    with monkeypatch.context() as m:
        m.syspath_prepend(str(tmp_path))

        importlib.import_module("out_nested")
        importlib.import_module("out_nested.a.b.c.thing2_pb2")
        importlib.import_module("out_nested.d.thing1_pb2")

    # check that we created packages in the correct locations
    assert out_nested.joinpath("__init__.py").exists()
    assert out_nested.joinpath("a", "__init__.py").exists()
    assert out_nested.joinpath("a", "b", "__init__.py").exists()
    assert out_nested.joinpath("a", "b", "c", "__init__.py").exists()
    assert out_nested.joinpath("d", "__init__.py").exists()


@pytest.mark.xfail(
    condition=sys.version_info[:2] == (3, 10),
    raises=subprocess.CalledProcessError,
    reason="grpc-cpp cannot be installed with conda using Python 3.10",
)
def test_grpc_buf(
    cli: CliRunner,
    tmp_path: Path,
    thing1: Path,
    thing2: Path,
    buf_yaml: Path,
    buf_gen_yaml_grpc: Path,
    thing_service: Path,
    out_grpc: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    subprocess.check_call(["buf", "generate"])

    check_proto_out(out_grpc)

    result = cli.invoke(
        main,
        [
            "-o",
            str(out_grpc),
            "--in-place",
            "--create-package",
            "buf",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    service_module = out_grpc.joinpath("thing_service_pb2_grpc.py")
    assert service_module.exists()

    lines = service_module.read_text().splitlines()

    assert "from . import thing1_pb2 as thing1__pb2" in lines
    assert "import thing1_pb2 as thing1__pb2" not in lines

    assert "from . import thing2_pb2 as thing2__pb2" in lines
    assert "import thing2_pb2 as thing2__pb2" not in lines

    assert out_grpc.joinpath("__init__.py").exists()

    # check that we can import the thing
    with monkeypatch.context() as m:
        m.syspath_prepend(str(tmp_path))

        importlib.import_module("out_grpc.thing1_pb2")
        importlib.import_module("out_grpc.thing2_pb2")
        importlib.import_module("out_grpc.thing_service_pb2_grpc")


@pytest.mark.xfail(
    condition=sys.version_info[:2] == (3, 10),
    raises=subprocess.CalledProcessError,
    reason="grpc-cpp cannot be installed with conda using Python 3.10",
)
def test_grpc_buf_no_imports(
    cli: CliRunner,
    tmp_path: Path,
    buf_yaml: Path,
    buf_gen_yaml_grpc_no_imports: Path,
    no_imports_service: Path,
    out_grpc_no_imports: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    subprocess.check_call(["buf", "generate"])

    check_proto_out(out_grpc_no_imports)

    result = cli.invoke(
        main,
        [
            "-o",
            str(out_grpc_no_imports),
            "--in-place",
            "--create-package",
            "buf",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    service_module = out_grpc_no_imports.joinpath("no_imports_service_pb2_grpc.py")
    assert service_module.exists()

    assert out_grpc_no_imports.joinpath("__init__.py").exists()

    # check that we can import the thing
    with monkeypatch.context() as m:
        m.syspath_prepend(str(tmp_path))

        importlib.import_module("out_grpc_no_imports.no_imports_service_pb2_grpc")


@pytest.mark.xfail(
    condition=sys.version_info[:2] == (3, 10),
    raises=subprocess.CalledProcessError,
    reason="grpc-cpp cannot be installed with conda using Python 3.10",
)
def test_pyi(
    cli: CliRunner,
    tmp_path: Path,
    buf_yaml: Path,
    buf_gen_yaml_grpc_no_imports: Path,
    no_imports_service: Path,
    out_grpc_no_imports: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    subprocess.check_call(["buf", "generate"])

    check_proto_out(out_grpc_no_imports)

    result = cli.invoke(
        main,
        [
            "-o",
            str(out_grpc_no_imports),
            "--in-place",
            "--create-package",
            "buf",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0

    service_module = out_grpc_no_imports.joinpath("no_imports_service_pb2_grpc.py")
    assert service_module.exists()

    service_module_types = service_module.with_suffix(".pyi")
    assert service_module_types.exists()

    service_module_types_lines = service_module_types.read_text().splitlines()
    assert "no_imports_service_pb2" not in service_module_types_lines
    assert "from . import no_imports_service_pb2" in service_module_types_lines
    assert out_grpc_no_imports.joinpath("__init__.py").exists()

    # check that we can import the thing
    with monkeypatch.context() as m:
        m.syspath_prepend(str(tmp_path))

        importlib.import_module("out_grpc_no_imports.no_imports_service_pb2_grpc")


@pytest.mark.xfail(
    condition=sys.version_info[:2] == (3, 10),
    raises=subprocess.CalledProcessError,
    reason="grpc-cpp cannot be installed with conda using Python 3.10",
)
def test_pyi_with_imports(
    cli: CliRunner,
    tmp_path: Path,
    buf_yaml: Path,
    buf_gen_yaml_grpc_imports: Path,
    imports_service: Path,
    out_grpc_imports: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    subprocess.check_call(["buf", "generate"])

    check_proto_out(out_grpc_imports)

    result = cli.invoke(
        main,
        [
            "-o",
            str(out_grpc_imports),
            "--in-place",
            "--create-package",
            "buf",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0

    service_module = out_grpc_imports.joinpath("imports_service_pb2_grpc.py")
    assert service_module.exists()

    service_module_types = service_module.with_suffix(".pyi")
    assert service_module_types.exists()

    service_module_types_lines = service_module_types.read_text().splitlines()
    assert "imports_service_pb2" not in service_module_types_lines
    # this line should be in the code twice:
    # once for get_pb2, once for post_pb2
    assert service_module_types_lines.count("from . import requests") == 2

    # neither of the following two lines should be in the result
    assert "import requests.get_pb2" not in service_module_types_lines
    assert "import requests.post_pb2" not in service_module_types_lines

    assert out_grpc_imports.joinpath("__init__.py").exists()

    # check that we can import the thing
    with monkeypatch.context() as m:
        m.syspath_prepend(str(tmp_path))

        importlib.import_module("out_grpc_imports.imports_service_pb2_grpc")


def test_pyi_with_long_names(
    cli: CliRunner,
    tmp_path: Path,
    buf_yaml: Path,
    buf_gen_yaml_long_names: Path,
    out_long_names: Path,
    long_names_proto: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    subprocess.check_call(["buf", "generate"])

    assert list(out_long_names.rglob("*.pyi"))
    assert all(path.read_text() for path in out_long_names.rglob("*.pyi"))

    for _ in range(2):
        result = cli.invoke(
            main,
            [
                "-o",
                str(out_long_names),
                "--in-place",
                "--create-package",
                "buf",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

import importlib
import subprocess
import sys

import pytest
from click.testing import CliRunner

from .conftest import ProtoletariatFixture, check_import_lines


def test_basic_cli(cli: CliRunner, basic_cli: ProtoletariatFixture) -> None:
    result = basic_cli.generate(cli)
    assert result.exit_code == 0

    basic_cli.check_proto_out()

    expected_lines = [
        "from . import other_pb2 as other__pb2",
        "from .baz import bizz_buzz_pb2 as baz_dot_bizz__buzz__pb2",
    ]

    check_import_lines(result, expected_lines)

    result = basic_cli.generate(cli, args=["--in-place", "--create-package"])
    assert result.exit_code == 0

    with basic_cli.patched_syspath:
        importlib.import_module(basic_cli.package_name)
        importlib.import_module(f"{basic_cli.package_name}.this_pb2")
        importlib.import_module(f"{basic_cli.package_name}.other_pb2")


def test_nested(cli: CliRunner, nested: ProtoletariatFixture) -> None:
    result = nested.generate(cli)
    assert result.exit_code == 0

    nested.check_proto_out()

    result = nested.generate(cli, args=["--in-place", "--create-package"])
    assert result.exit_code == 0

    # check that we can import nested things
    with nested.patched_syspath:
        importlib.import_module(nested.package_name)
        importlib.import_module(f"{nested.package_name}.d")
        importlib.import_module(f"{nested.package_name}.d.thing1_pb2")
        importlib.import_module(f"{nested.package_name}.a")
        importlib.import_module(f"{nested.package_name}.a.b")
        importlib.import_module(f"{nested.package_name}.a.b.c")
        importlib.import_module(f"{nested.package_name}.a.b.c.thing2_pb2")


@pytest.mark.xfail(
    condition=sys.version_info[:2] == (3, 10),
    raises=subprocess.CalledProcessError,
    reason="grpc-cpp cannot be installed with conda using Python 3.10",
)
def test_thing_service(cli: CliRunner, thing_service: ProtoletariatFixture) -> None:
    result = thing_service.generate(cli)
    assert result.exit_code == 0

    thing_service.check_proto_out()

    result = thing_service.generate(cli, args=["--in-place", "--create-package"])
    assert result.exit_code == 0

    service_module = thing_service.package_dir.joinpath("thing_service_pb2_grpc.py")
    assert service_module.exists()

    lines = service_module.read_text().splitlines()

    assert "from . import thing1_pb2 as thing1__pb2" in lines
    assert "import thing1_pb2 as thing1__pb2" not in lines

    assert "from . import thing2_pb2 as thing2__pb2" in lines
    assert "import thing2_pb2 as thing2__pb2" not in lines

    # check that we can import the thing
    with thing_service.patched_syspath:
        importlib.import_module(f"{thing_service.package_name}.thing1_pb2")
        importlib.import_module(f"{thing_service.package_name}.thing2_pb2")
        importlib.import_module(f"{thing_service.package_name}.thing_service_pb2_grpc")


@pytest.mark.xfail(
    condition=sys.version_info[:2] == (3, 10),
    raises=subprocess.CalledProcessError,
    reason="grpc-cpp cannot be installed with conda using Python 3.10",
)
def test_grpc(cli: CliRunner, grpc_imports: ProtoletariatFixture) -> None:
    result = grpc_imports.generate(cli)
    assert result.exit_code == 0

    grpc_imports.check_proto_out()

    result = grpc_imports.generate(cli, args=["--in-place", "--create-package"])
    assert result.exit_code == 0

    service_module = grpc_imports.package_dir.joinpath("imports_service_pb2_grpc.py")
    assert service_module.exists()

    service_module_types = service_module.with_suffix(".pyi")
    assert service_module_types.exists()

    service_module_types_text = service_module_types.read_text()
    assert "import imports_service_pb2" not in service_module_types_text
    # this line should be in the code twice:
    # once for get_pb2, once for post_pb2
    assert service_module_types_text.count("from . import requests") == 2

    # neither of the following two lines should be in the result
    assert "import requests.get_pb2" not in service_module_types_text
    assert "import requests.post_pb2" not in service_module_types_text

    with grpc_imports.patched_syspath:
        importlib.import_module(f"{grpc_imports.package_name}.imports_service_pb2_grpc")


@pytest.mark.xfail(
    condition=sys.version_info[:2] == (3, 10),
    raises=subprocess.CalledProcessError,
    reason="grpc-cpp cannot be installed with conda using Python 3.10",
)
def test_grpc_no_imports(
    cli: CliRunner,
    no_imports_service: ProtoletariatFixture,
) -> None:
    result = no_imports_service.generate(cli)
    assert result.exit_code == 0

    no_imports_service.check_proto_out()

    result = no_imports_service.generate(cli, args=["--in-place", "--create-package"])
    assert result.exit_code == 0

    service_module_types = no_imports_service.package_dir.joinpath(
        "no_imports_service_pb2_grpc.pyi"
    )
    assert service_module_types.exists()

    service_module_types_lines = service_module_types.read_text().splitlines()
    assert "import no_imports_service_pb2" not in service_module_types_lines
    assert "from . import no_imports_service_pb2" in service_module_types_lines

    with no_imports_service.patched_syspath:
        importlib.import_module(
            f"{no_imports_service.package_name}.no_imports_service_pb2_grpc"
        )


def test_pyi_with_long_names(cli: CliRunner, long_names: ProtoletariatFixture) -> None:
    result = long_names.generate(cli)
    assert result.exit_code == 0

    assert list(long_names.package_dir.rglob("*.pyi"))
    assert all(path.read_text() for path in long_names.package_dir.rglob("*.pyi"))

    for _ in range(2):
        result = long_names.generate(cli, args=["--in-place", "--create-package"])
        assert result.exit_code == 0


def test_ignored_imports(cli: CliRunner, ignored_imports: ProtoletariatFixture) -> None:
    result = ignored_imports.generate(
        cli,
        args=["-e", "igno*", "--in-place", "--create-package"],
    )
    assert result.exit_code == 0

    assert list(ignored_imports.package_dir.rglob("*.py"))

    mod = ignored_imports.package_dir.joinpath("ignored_import_pb2.py")
    text = mod.read_text()
    lines = text.splitlines()

    ignored_google_line = (
        "from .google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2"
    )
    ignored_custom_line = "from . import ignored_pb2 as ignored__pb2"
    lines = text.splitlines()

    assert ignored_google_line not in lines
    assert ignored_custom_line not in lines

    google_line = (
        "from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2"
    )
    custom_line = "import ignored_pb2 as ignored__pb2"
    assert google_line in lines
    assert custom_line in lines

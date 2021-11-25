import json
from pathlib import Path

import pytest
from click.testing import CliRunner


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


@pytest.fixture
def thing_service_text() -> str:
    return """
// thing_service.proto
syntax = "proto3";

import "thing1.proto";
import "thing2.proto";

package things;

service ThingService {
    rpc GetThing1(Thing1) returns (Thing1) {}
    rpc GetThing2(Thing2) returns (Thing2) {}
}
"""


@pytest.fixture
def thing_service(thing_service_text: str, tmp_path: Path) -> Path:
    p = tmp_path.joinpath("thing_service.proto")
    p.write_text(thing_service_text)
    return p


@pytest.fixture
def buf_yaml(tmp_path: Path) -> Path:
    p = tmp_path.joinpath("buf.yaml")
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "lint": {"use": ["DEFAULT"]},
                "breaking": {"use": ["FILE"]},
            },
        )
    )
    return p


@pytest.fixture
def out_grpc(tmp_path: Path) -> Path:
    out = tmp_path / "out_grpc"
    out.mkdir()
    return out


@pytest.fixture
def out(tmp_path: Path) -> Path:
    out = tmp_path / "out"
    out.mkdir()
    return out


@pytest.fixture
def out_nested(tmp_path: Path) -> Path:
    out = tmp_path / "out_nested"
    out.mkdir()
    return out


@pytest.fixture
def buf_gen_yaml_grpc(tmp_path: Path, out_grpc: Path) -> Path:
    p = tmp_path.joinpath("buf.gen.yaml")
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "plugins": [
                    {
                        "name": "python",
                        "out": str(out_grpc),
                    },
                    {
                        "name": "grpc_python",
                        "out": str(out_grpc),
                        "path": "grpc_python_plugin",
                    },
                ],
            },
        )
    )
    return p


@pytest.fixture
def buf_gen_yaml(tmp_path: Path, out: Path) -> Path:
    p = tmp_path.joinpath("buf.gen.yaml")
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "plugins": [
                    {
                        "name": "python",
                        "out": str(out),
                    }
                ],
            },
        )
    )
    return p


@pytest.fixture
def buf_gen_yaml_nested(tmp_path: Path, out_nested: Path) -> Path:
    p = tmp_path.joinpath("buf.gen.yaml")
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "plugins": [
                    {
                        "name": "python",
                        "out": str(out_nested),
                    }
                ],
            },
        )
    )
    return p


@pytest.fixture
def out_grpc_no_imports(tmp_path: Path) -> Path:
    out = tmp_path / "out_grpc_no_imports"
    out.mkdir()
    return out


@pytest.fixture
def no_imports_service_text() -> str:
    return """
// no_imports_service.proto
syntax = "proto3";

package no_imports.a.b;

message Request {}
message Response {}

service NoImportsService {
    rpc Get(Request) returns (Response) {}
}
"""


@pytest.fixture
def no_imports_service(no_imports_service_text: str, tmp_path: Path) -> Path:
    p = tmp_path.joinpath("no_imports_service.proto")
    p.write_text(no_imports_service_text)
    return p


@pytest.fixture
def buf_gen_yaml_grpc_no_imports(tmp_path: Path, out_grpc_no_imports: Path) -> Path:
    p = tmp_path.joinpath("buf.gen.yaml")
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "plugins": [
                    {
                        "name": "python",
                        "out": str(out_grpc_no_imports),
                    },
                    {
                        "name": "grpc_python",
                        "out": str(out_grpc_no_imports),
                        "path": "grpc_python_plugin",
                    },
                ],
            },
        )
    )
    return p

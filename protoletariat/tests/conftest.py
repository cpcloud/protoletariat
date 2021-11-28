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
                    {
                        "name": "mypy",
                        "out": str(out_grpc_no_imports),
                    },
                    {
                        "name": "mypy_grpc",
                        "out": str(out_grpc_no_imports),
                    },
                ],
            },
        )
    )
    return p


@pytest.fixture
def out_grpc_imports(tmp_path: Path) -> Path:
    out = tmp_path / "out_grpc_imports"
    out.mkdir()
    return out


@pytest.fixture(scope="session")
def imports_service_text() -> str:
    return """
// no_imports_service.proto
syntax = "proto3";

import "requests/get.proto";
import "requests/post.proto";

package imports_service;

service ImportsService {
    rpc Get(msg.GetRequest) returns (msg.GetResponse) {}
    rpc Post(msg.PostRequest) returns (msg.PostResponse) {}
}
"""


@pytest.fixture(scope="session")
def requests_get_proto_text() -> str:
    return """
syntax = "proto3";

package imports_service.msg;

message GetRequest {}
message GetResponse {}
"""


@pytest.fixture()
def requests_get_proto(tmp_path: Path, requests_get_proto_text: str) -> Path:
    requests_dir = tmp_path.joinpath("requests")
    requests_dir.mkdir(exist_ok=True)
    p = requests_dir.joinpath("get.proto")
    p.write_text(requests_get_proto_text)
    return p


@pytest.fixture(scope="session")
def requests_post_proto_text() -> str:
    return """
syntax = "proto3";

package imports_service.msg;

message PostRequest {}
message PostResponse {}
"""


@pytest.fixture()
def requests_post_proto(tmp_path: Path, requests_post_proto_text: str) -> Path:
    requests_dir = tmp_path.joinpath("requests")
    requests_dir.mkdir(exist_ok=True)
    p = requests_dir.joinpath("post.proto")
    p.write_text(requests_post_proto_text)
    return p


@pytest.fixture
def imports_service(
    imports_service_text: str,
    tmp_path: Path,
    requests_get_proto: Path,
    requests_post_proto: Path,
) -> Path:
    p = tmp_path.joinpath("imports_service.proto")
    p.write_text(imports_service_text)
    return p


@pytest.fixture
def buf_gen_yaml_grpc_imports(tmp_path: Path, out_grpc_imports: Path) -> Path:
    p = tmp_path.joinpath("buf.gen.yaml")
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "plugins": [
                    {
                        "name": "python",
                        "out": str(out_grpc_imports),
                    },
                    {
                        "name": "grpc_python",
                        "out": str(out_grpc_imports),
                        "path": "grpc_python_plugin",
                    },
                    {
                        "name": "mypy",
                        "out": str(out_grpc_imports),
                    },
                    {
                        "name": "mypy_grpc",
                        "out": str(out_grpc_imports),
                    },
                ],
            },
        )
    )
    return p


@pytest.fixture(scope="session")
def long_names_text() -> str:
    # taken from https://github.com/substrait-io/substrait
    return """
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


@pytest.fixture
def out_long_names(tmp_path: Path) -> Path:
    out = tmp_path / "out_long_names"
    out.mkdir()
    return out


@pytest.fixture
def long_names_proto(tmp_path: Path, long_names_text: str) -> Path:
    p = tmp_path / "function.proto"
    p.write_text(long_names_text)
    return p


@pytest.fixture
def buf_gen_yaml_long_names(tmp_path: Path, out_long_names: Path) -> Path:
    p = tmp_path / "buf.gen.yaml"
    p.write_text(
        json.dumps(
            {
                "version": "v1",
                "plugins": [
                    {
                        "name": "mypy",
                        "out": str(out_long_names),
                    },
                ],
            },
        )
    )
    return p

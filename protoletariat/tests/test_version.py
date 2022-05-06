from pathlib import Path

import tomli

import protoletariat


def test_version() -> None:
    path = Path(__file__).parent.parent.parent.joinpath("pyproject.toml")
    pyproject = tomli.loads(path.read_text())
    assert protoletariat.__version__ == pyproject["tool"]["poetry"]["version"]

import itertools
from typing import Iterable

import pytest

from protoletariat.rewrite import build_rewrites


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
        pytest.param(
            "a_b/c",
            "foo_bar/baz/bizz",
            [
                "from ..foo_bar.baz import bizz_pb2 as foo__bar_dot_baz_dot_bizz__pb2",
                "from .. import foo_bar",
            ],
            id="underscore_package",
        ),
    ],
)
def test_build_import_rewrites(proto: str, dep: str, expecteds: Iterable[str]) -> None:
    rewrites = build_rewrites(proto, dep)
    for (_, new), expected in itertools.zip_longest(rewrites, expecteds):
        assert new == expected

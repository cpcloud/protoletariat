from __future__ import annotations

import ast
import collections
import collections.abc
from ast import AST
from typing import Any, Callable, NamedTuple, Sequence, Union

Node = Union[AST, Sequence[AST]]


class Replacement(NamedTuple):
    old: str
    new: str


def _is_iterable(value: Any) -> bool:  # type: ignore[misc]
    """Return whether `value` is a non-string iterable."""
    return not isinstance(value, str) and isinstance(value, collections.abc.Iterable)


def matches(value: Node, pattern: Node) -> bool:
    """Check whether `value` matches `pattern`.

    Parameters
    ----------
    value
        Instance to match
    pattern
        Pattern to match against
    """
    # types must match exactly
    if type(value) != type(pattern):
        return False

    # recur into lists
    if _is_iterable(value) and _is_iterable(pattern):
        assert isinstance(
            value, collections.abc.Iterable
        ), f"value is not a non-str iterable {type(value).__name__}"
        assert isinstance(
            pattern, collections.abc.Iterable
        ), f"pattern is not a non-str iterable {type(pattern).__name__}"
        return all(map(matches, value, pattern))

    # primitive value, such as None, True, False, etc.
    if not isinstance(value, AST) and not isinstance(pattern, AST):
        return value == pattern

    assert isinstance(value, AST), f"value is not an AST node: {type(value).__name__}"
    assert isinstance(
        pattern, AST
    ), f"pattern is not an AST node: {type(pattern).__name__}"

    fields = [
        (field, getattr(pattern, field))
        for field in pattern._fields
        if hasattr(pattern, field)
    ]
    for field_name, field_value in fields:
        if not matches(getattr(value, field_name), field_value):
            return False
    return True


class Rewriter:
    """AST pattern matching to enable rewrite rules."""

    def __init__(self) -> None:
        self.funcs: list[tuple[AST, Callable[[AST], AST]]] = []

    def register(
        self, pattern: AST
    ) -> Callable[[Callable[[AST], AST]], Callable[[AST], AST]]:
        def wrapper(f: Callable[[AST], AST]) -> Callable[[AST], AST]:
            self.funcs.append((pattern, f))
            return f

        return wrapper

    def __call__(self, node: AST) -> AST:
        for pattern, func in self.funcs:
            if matches(node, pattern):
                return func(node)
        return node


def build_import_rewrite(proto: str, dep: str) -> Replacement:
    """Construct a replacement import for `dep`.

    Parameters
    ----------
    dep
        The `name` field of a `FileDescriptorProto` message, stripped
        of its ``.proto`` suffix.

    Returns
    -------
    Replacement
        A named tuple of the old import and its replacement
    """
    parts = dep.split("/")

    *import_parts, part = parts

    # compute the number of dots needed to get to the package root
    num_leading_dots = proto.count("/") + 1
    leading_dots = "." * num_leading_dots
    last_part = "__".join(f"{part}_pb2".split("_"))

    if not import_parts:
        # underscores are doubled by protoc/buf
        old = f"import {part}_pb2 as {last_part}"
        new = f"from {leading_dots} import {part}_pb2 as {last_part}"
    else:
        from_ = ".".join(import_parts)
        as_ = f"{'_dot_'.join(import_parts)}_dot_{last_part}"

        old = f"from {from_} import {part}_pb2 as {as_}"
        new = f"from {leading_dots}{from_} import {part}_pb2 as {as_}"

    return Replacement(old=old, new=new)


class ImportRewriter(ast.NodeTransformer):
    """A NodeTransformer to apply rewrite rules."""

    def __init__(self) -> None:
        self.rewrite = Rewriter()

    def register_import_rewrite(self, replacement: Replacement) -> None:
        """Register a rewrite rule for turning `old` into `new`."""
        (old_import,) = ast.parse(replacement.old).body
        (new_import,) = ast.parse(replacement.new).body

        def _rewrite(_: AST, new_import: AST = new_import) -> AST:
            return new_import

        if all(not matches(old_import, pat) for pat, _ in self.rewrite.funcs):
            self.rewrite.register(old_import)(_rewrite)

        assert sum(matches(old_import, pat) for pat, _ in self.rewrite.funcs) == 1

    def visit_Import(self, node: ast.Import) -> AST:
        return self.rewrite(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> AST:
        return self.rewrite(node)

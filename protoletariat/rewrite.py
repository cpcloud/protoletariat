from __future__ import annotations

import ast
import collections
from typing import Any, Callable, NamedTuple, Sequence, Union

Node = Union[ast.AST, Sequence[ast.AST]]


class Replacement(NamedTuple):
    old: str
    new: str


def _is_iterable(value: Any) -> bool:
    return not isinstance(value, str) and isinstance(value, collections.Iterable)


def matches(value: Node, pattern: Node):
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
            value, collections.Iterable
        ), f"value is not a non-str iterable {type(value).__name__}"
        assert isinstance(
            pattern, collections.Iterable
        ), f"pattern is not a non-str iterable {type(pattern).__name__}"
        return all(map(matches, value, pattern))

    # primitive value, such as None, True, False, etc.
    if not isinstance(value, ast.AST) and not isinstance(pattern, ast.AST):
        return value == pattern

    assert isinstance(
        value, ast.AST
    ), f"value is not an AST node: {type(value).__name__}"
    assert isinstance(
        pattern, ast.AST
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
        self.funcs: list[tuple[ast.AST, Callable[[ast.AST], ast.AST]]] = []

    def register(
        self, pattern: ast.AST
    ) -> Callable[[Callable[[ast.AST], ast.AST]], Callable[[ast.AST], ast.AST]]:
        def wrapper(f: Callable[[ast.AST], ast.AST]) -> Callable[[ast.AST], ast.AST]:
            self.funcs.append((pattern, f))
            return f

        return wrapper

    def __call__(self, node: ast.AST) -> ast.AST:
        for pattern, func in self.funcs:
            if matches(node, pattern):
                return func(node)
        return node


rewrite = Rewriter()


def build_import_rewrite(dep: str) -> Replacement:
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

    import_parts = []
    for part in parts[:-1]:
        import_parts.append(part)

    if not import_parts:
        (part,) = parts
        old = f"import {part}_pb2 as {part}__pb2"
        new = f"from . import {part}_pb2 as {part}__pb2"
    else:
        last_piece = "__".join(f"{parts[-1]}_pb2".split("_"))

        from_ = ".".join(import_parts)
        as_ = f"{'_dot_'.join(import_parts)}_dot_{last_piece}"

        old = f"from {from_} import {parts[-1]}_pb2 as {as_}"
        new = f"from .{from_} import {parts[-1]}_pb2 as {as_}"

    return Replacement(old=old, new=new)


def register_import_rewrite(replacement: Replacement) -> None:
    """Register a rewrite rule for turning `old` into `new`."""
    (old_import,) = ast.parse(replacement.old).body
    (new_import,) = ast.parse(replacement.new).body

    def _rewrite(_: ast.AST, new_import: ast.AST = new_import) -> ast.AST:
        return new_import

    rewrite.register(old_import)(_rewrite)


class ImportRewriter(ast.NodeTransformer):
    """A NodeTransformer to apply rewrite rules."""

    def visit_Import(self, node: ast.Import) -> ast.ImportFrom:
        return rewrite(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        return rewrite(node)

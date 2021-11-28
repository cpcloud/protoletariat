from __future__ import annotations

import collections
import collections.abc
import typing
from typing import Any, Callable, NamedTuple, Sequence, Union

import astunparse
from typed_ast import ast3 as ast
from typed_ast.ast3 import AST

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

    return all(
        matches(getattr(value, field), getattr(pattern, field))
        for field in pattern._fields
        if hasattr(pattern, field)
    )


class ASTRewriter:
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


def build_rewrites(proto: str, dep: str) -> Sequence[Replacement]:
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

    return [
        Replacement(old=old, new=new),
        Replacement(
            old=f"import {'.'.join(parts)}_pb2",
            new=(
                f"from {leading_dots or '.'} import {parts[0]}"
                + "_pb2" * (not import_parts)
            ),
        ),
    ]


class ImportNodeTransformer(ast.NodeTransformer):
    """A NodeTransformer to apply rewrite rules."""

    def __init__(self, ast_rewriter: ASTRewriter) -> None:
        self.ast_rewriter = ast_rewriter

    def visit_Import(self, node: ast.Import) -> AST:
        return self.ast_rewriter(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> AST:
        return self.ast_rewriter(node)


class ASTImportRewriter:
    def __init__(self) -> None:
        self.node_transformer = ImportNodeTransformer(ASTRewriter())

    def register_rewrite(self, replacement: Replacement) -> None:
        """Register a rewrite rule for turning `old` into `new`."""
        (old_node,) = typing.cast(ast.Module, ast.parse(replacement.old)).body
        (new_node,) = typing.cast(ast.Module, ast.parse(replacement.new)).body

        def _rewrite(_: AST, repl: AST = new_node) -> AST:
            return repl

        funcs = self.node_transformer.ast_rewriter.funcs
        if all(not matches(old_node, pat) for pat, _ in funcs):
            self.node_transformer.ast_rewriter.register(old_node)(_rewrite)
        assert (
            sum(matches(old_node, pat) for pat, _ in funcs) == 1
        ), f"more than one rewrite rule found for pattern `{replacement.old}`"

    def rewrite(self, src: str) -> str:
        return astunparse.unparse(self.node_transformer.visit(ast.parse(src)))

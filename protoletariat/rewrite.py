from __future__ import annotations

import ast
import collections
import collections.abc
import typing
from ast import AST
from typing import Any, Callable, MutableSet, NamedTuple, Sequence, Union

try:
    from ast import unparse as astunparse
except ImportError:
    from astunparse import unparse as astunparse  # type: ignore[no-redef]

Node = Union[AST, Sequence[AST]]


class Replacement(NamedTuple):
    """A mapping from an old import to a new import."""

    old: str
    new: str


def _is_iterable(value: Any) -> bool:  # type: ignore[misc]
    """Return whether `value` is a non-string iterable.

    Examples
    --------
    >>> _is_iterable(1)
    False
    >>> _is_iterable([1])
    True
    >>> _is_iterable("a")
    False
    >>> _is_iterable(["a"])
    True
    """
    return not isinstance(value, str) and isinstance(value, collections.abc.Iterable)


def matches(value: Node, pattern: Node) -> bool:
    """Check whether `value` matches `pattern`.

    Parameters
    ----------
    value
        Instance to match
    pattern
        Pattern to match against

    Returns
    -------
    bool
        Whether `value` matches `pattern`

    Examples
    --------
    >>> import ast
    >>> node = ast.parse("x = 1")
    >>> pattern = node
    >>> matches(node, pattern)
    True
    >>> node = ast.parse("x = 2")
    >>> matches(node, pattern)
    False
    """
    # types must match exactly
    if type(value) != type(pattern):
        return False

    # recur into non-str sequences
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


ASTTransform = Callable[[AST], AST]


class ASTRewriter:
    """AST pattern matching to enable rewrite rules."""

    def __init__(self) -> None:
        self.funcs: list[tuple[AST, ASTTransform]] = []

    def register(self, pattern: AST) -> Callable[[ASTTransform], ASTTransform]:
        """Register a callable to rewrite `pattern`."""

        def wrapper(f: ASTTransform) -> ASTTransform:
            self.funcs.append((pattern, f))
            return f

        return wrapper

    def rewrite(self, node: AST) -> AST:
        """Rewrite `node` if it matches a registered pattern.

        Examples
        --------
        >>> rewriter = ASTRewriter()
        >>> pattern = ast.parse("x = 1")
        >>> @rewriter.register(pattern)
        ... def make_it_two(node):
        ...     return ast.parse("x = 2")
        ...
        >>> node = ast.parse("x = 1")
        >>> print(astunparse(node))  # doctest: +NORMALIZE_WHITESPACE
        x = 1
        >>> rewritten = rewriter.rewrite(node)
        >>> print(astunparse(rewritten))  # doctest: +NORMALIZE_WHITESPACE
        x = 2
        """
        try:
            return next(
                func(node) for pattern, func in self.funcs if matches(node, pattern)
            )
        except StopIteration:
            return node


def build_rewrites(proto: str, dep: str) -> list[Replacement]:
    """Construct a replacement import for `dep`.

    Parameters
    ----------
    proto
        The dependent protobuf path.
    dep
        The `name` field of a `FileDescriptorProto` message, stripped
        of its ``.proto`` suffix.

    Returns
    -------
    list[Replacement]
        A list of mapping from old code to new code

    Examples
    --------
    >>> from pprint import pprint
    >>> proto = "a/b/c"
    >>> dep = "foo/bar"
    >>> pprint(build_rewrites(proto, dep))
    [Replacement(old='from foo import bar_pb2 as foo_dot_bar__pb2', new='from ...foo import bar_pb2 as foo_dot_bar__pb2'),
     Replacement(old='import foo.bar_pb2', new='from ... import foo')]
    """
    parts = dep.split("/")

    *import_parts, part = parts

    # compute the number of dots needed to get to the package root relative to
    # the dependent proto file
    num_leading_dots = proto.count("/") + 1
    leading_dots = "." * num_leading_dots
    last_part = "__".join(f"{part}_pb2".split("_"))

    if not import_parts:
        # underscores are doubled by codegen
        old = f"import {part}_pb2 as {last_part}"
        new = f"from {leading_dots} import {part}_pb2 as {last_part}"
    else:
        from_ = ".".join(import_parts)
        fake_dotted_path = "_dot_".join(
            part.replace("_", "__") for part in import_parts
        )
        as_ = f"{fake_dotted_path}_dot_{last_part}"

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
        # track the results we've produced to avoid duplication of imports
        self.seen: MutableSet[str] = set()

    def visit_Import(self, node: ast.AST) -> AST | None:
        result = self.ast_rewriter.rewrite(node)
        code = astunparse(result)
        if code not in self.seen:
            self.seen.add(code)
            return result
        return None

    visit_ImportFrom = visit_Import


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
        self.node_transformer.seen.clear()
        return astunparse(self.node_transformer.visit(ast.parse(src)))

# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""The spec an entry over dimensions with members lowers as, where it needs their members by name.

Two cases read an entry over its members rather than over its tuples: two of
its dimensions share a member, as in ``dims: [connection, active]``, or a
step runs along a member, as ``shift(output, along=period)`` does on
``output`` over ``active``. Each such entry lowers as the same entry over the
members, with ``where:`` the dimensions it listed, which is the spelling a
dimension without an order and without a shared member must write. Every
other entry keeps its dimensions, and meets these by name.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from mathspec._expression_parser import FunctionCallNode, NameNode, nodes, parse_expression
from mathspec.errors import LanguageError
from mathspec.program import And, Mask, RelationDefined

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from mathspec.program import Condition
    from mathspec.spec import ConstraintSpec, ExpressionSpec, ParameterSpec, Spec, VariableSpec

    type Framed = ParameterSpec | VariableSpec | ConstraintSpec | ExpressionSpec

_SECTIONS = ('parameters', 'variables', 'constraints', 'expressions')
_STEP = re.compile(r'\balong\s*=\s*([A-Za-z_]\w*)|\bposition\(\s*([A-Za-z_]\w*)')

type Entry = tuple[str, str]


def flat_spec(spec: Spec) -> tuple[Spec, dict[str, Mask]]:
    """*spec* with each entry that needs its members by name declared over them, and the domain of each such parameter.

    Returns *spec* itself, and no domain, where no entry needs it. A
    parameter's domain is the tuples its ``dims:`` listed: a tool refuses its
    data row outside them, where the ``where:`` of the flat spelling drops it.
    """
    from mathspec.spec import Spec

    tuples = {name: frozenset(dim for _, dim in d.members) for name, d in spec.dimensions.items() if d.members}
    entries: dict[Entry, Framed] = {
        (section, name): entry
        for section in _SECTIONS
        for name, entry in cast('Mapping[str, Framed]', getattr(spec, section)).items()
        if set(entry.dims or ()) & set(tuples)
    }
    flat = _flattened(entries, tuples, spec)
    if not flat:
        return spec, {}
    written = spec.to_dict()
    for (section, name), over in flat.items():
        declared = cast('dict[str, dict[str, object]]', written[section])
        declared[name] = _over_members(section, declared[name], entries[section, name], over, tuples)
    domains = {
        name: _domain(entries[section, name].dims or (), tuples) for section, name in flat if section == 'parameters'
    }
    return Spec.model_validate(written), domains


def _flattened(
    entries: Mapping[Entry, Framed], tuples: Mapping[str, frozenset[str]], spec: Spec
) -> dict[Entry, frozenset[str]]:
    """Each entry to read over its members, with the dimensions it lists that it reads so.

    An entry whose dimensions share a member, an entry that steps along a
    member of one of its dimensions, and an entry that a step reads so.
    """
    stepped = _stepped(spec, tuples, entries)
    flat = {
        key
        for key, entry in entries.items()
        if _shares(entry.dims or (), tuples) or _steps(entry, tuples) or key[1] in stepped
    }
    return {key: frozenset(d for d in entries[key].dims or () if d in tuples) for key in flat}


def _shares(dims: Iterable[str], tuples: Mapping[str, frozenset[str]]) -> bool:
    """Whether two of *dims* reach one member: two dimensions with members, or one beside a member of its own."""
    reached = [member for d in dims for member in tuples.get(d, {d})]
    return len(reached) != len(set(reached))


def _members(entry: Framed, tuples: Mapping[str, frozenset[str]]) -> set[str]:
    """The members of the dimensions *entry* is over, less those it is over as dimensions of their own."""
    dims = set(entry.dims or ())
    return {m for d in dims if d in tuples for m in tuples[d]} - dims


def _steps(entry: Framed, tuples: Mapping[str, frozenset[str]]) -> bool:
    """Whether the entry steps along a member of one of its dimensions, which a tuple has no order to step along."""
    members = _members(entry, tuples)
    return any(set(found) & members for found in _STEP.findall(' '.join(_texts(entry))))


def _stepped(spec: Spec, tuples: Mapping[str, frozenset[str]], entries: Mapping[Entry, Framed]) -> set[str]:
    """The entries a ``shift`` or ``sum_back`` steps along a member of one of their dimensions, anywhere in the file."""
    members_of = {name: _members(entry, tuples) for (_, name), entry in entries.items()}
    texts = [text for entry in _every_entry(spec) for text in _texts(entry)]
    if spec.objective is not None:
        texts.append(spec.objective.expression)
    stepped: set[str] = set()
    for text in texts:
        try:
            tree = parse_expression(text)
        except LanguageError:
            continue
        for call in nodes(tree):
            if not (isinstance(call, FunctionCallNode) and call.name in ('shift', 'sum_back')):
                continue
            if not isinstance(along := call.kwargs.get('along'), NameNode):
                continue
            read = {n.name for n in nodes(*call.args) if isinstance(n, NameNode)}
            stepped |= {name for name in read & set(members_of) if along.name in members_of[name]}
    return stepped


def _every_entry(spec: Spec) -> Iterator[Framed]:
    """Every entry of the four sections that declare ``dims:``."""
    for section in _SECTIONS:
        yield from cast('Mapping[str, Framed]', getattr(spec, section)).values()


def _texts(entry: Framed) -> Iterator[str]:
    """Every expression and condition *entry* writes."""
    for key in ('where', 'expression', 'otherwise'):
        if isinstance(text := getattr(entry, key, None), str):
            yield text
    if (bounds := getattr(entry, 'bounds', None)) is not None:
        yield from (side for side in (bounds.lower, bounds.upper) if isinstance(side, str))
    for case in getattr(entry, 'cases', {}).values():
        yield case.when
        if isinstance(case.expression, str):
            yield case.expression


def _over_members(
    section: str, written: dict[str, object], entry: Framed, over: frozenset[str], tuples: Mapping[str, frozenset[str]]
) -> dict[str, object]:
    """The written *entry* over the members of the dimensions *over* names, confined to them by ``where:``.

    A named expression takes no ``where:``, so it is over the members alone,
    and reads absent wherever the entries in its body are.
    """
    flat = dict(written)
    flat['dims'] = sorted({m for d in entry.dims or () for m in (tuples[d] if d in over else {d})})
    if section != 'expressions':
        listed = ' AND '.join(sorted(over))
        own = getattr(entry, 'where', None)
        flat['where'] = listed if own is None else f'({listed}) AND ({own})'
    return flat


def _domain(dims: Iterable[str], tuples: Mapping[str, frozenset[str]]) -> Mask:
    """The tuples a parameter's ``dims:`` listed, as the condition that holds at its domain."""
    listed: list[Condition] = [RelationDefined(d, tuple(sorted(tuples[d]))) for d in sorted(dims) if d in tuples]
    root = listed[0]
    for atom in listed[1:]:
        root = And(root, atom)
    return Mask(root)

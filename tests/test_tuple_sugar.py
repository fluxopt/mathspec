# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A dimension's members read by name: each shorter spelling builds the program of the spelling it stands for.

A spelling that names a member where the tuple is meant loads as the call
through the tuple that it means, so the program cannot tell the two apart. A
parameter over two tuples is the one exception: its data is refused outside
the rows that both list.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mathspec import to_spec
from mathspec.program import And, Mask, RelationDefined
from tests.fixtures import EXAMPLES, varied

#: Units on the ports they have and in the periods they run, and the sites of
#: each unit: three tuples, two of which share `unit` with `connection`.
MODEL: dict[str, Any] = {
    'dimensions': {
        'unit': {},
        'port': {},
        'bus': {},
        'snapshot': {'dtype': 'int'},
        'period': {'dtype': 'int', 'ordered': True},
        'connection': {'over': ['unit', 'port']},
        'active': {'over': ['unit', 'period']},
        'site': {'over': ['unit', 'bus']},
    },
    'parameters': {
        'capacity': {'dims': ['unit']},
        'ramp': {'dims': ['unit']},
        'rating': {'dims': ['bus']},
    },
    'variables': {'flow': {'dims': ['connection', 'snapshot']}},
}


def _program(**patch: Any):
    return to_spec(varied(MODEL, **patch)).program


def _same(sugar: dict[str, Any], spelled: dict[str, Any], section: str, name: str) -> None:
    built, meant = _program(**sugar), _program(**spelled)
    assert getattr(built, section)[name] == getattr(meant, section)[name], 'the sugar builds what it stands for'


@pytest.mark.parametrize(
    ('sugar', 'spelled'),
    [
        pytest.param(
            'flow <= capacity', 'flow <= at(capacity, by=connection[unit])', id='a-constraint-reads-the-member'
        ),
        pytest.param(
            'flow * capacity <= 1', 'flow * at(capacity, by=connection[unit]) <= 1', id='a-product-reads-the-member'
        ),
        pytest.param('capacity >= flow', 'at(capacity, by=connection[unit]) >= flow', id='the-member-on-the-left'),
    ],
)
def test_an_operand_over_a_member_meets_the_tuple_by_name(sugar, spelled):
    """Was: refused, with the at() rewrite. A member operand is read at each tuple, as at(…, by=tuple[member]) reads it."""
    frame = ['connection', 'snapshot']
    _same(
        {'constraints.c': {'dims': frame, 'expression': sugar}},
        {'constraints.c': {'dims': frame, 'expression': spelled}},
        'constraints',
        'c',
    )


def test_a_member_meets_the_tuple_in_the_objective():
    built = _program(objective={'expression': 'sum(flow * capacity)'}).objective
    meant = _program(objective={'expression': 'sum(flow * at(capacity, by=connection[unit]))'}).objective
    assert built == meant, 'the objective reads the member at each tuple too'


@pytest.mark.parametrize(
    ('dims', 'sugar', 'spelled'),
    [
        pytest.param(
            ['snapshot', 'unit'],
            'sum(flow, over=port)',
            'sum(flow, over=connection, by=connection[unit])',
            id='one-member-summed-away',
        ),
        pytest.param(
            ['snapshot'], 'sum(flow, over=[port, unit])', 'sum(flow, over=connection)', id='every-member-summed-away'
        ),
        pytest.param(
            ['unit'],
            'sum(flow, over=[port, snapshot])',
            'sum(flow, over=[connection, snapshot], by=connection[unit])',
            id='a-member-beside-a-plain-dimension',
        ),
    ],
)
def test_a_sum_over_a_member_sums_the_tuple_grouped_by_the_rest(dims, sugar, spelled):
    """Was: refused, with the sum through the tuple as the rewrite."""
    _same(
        {'constraints.c': {'dims': dims, 'expression': f'{sugar} <= 1'}},
        {'constraints.c': {'dims': dims, 'expression': f'{spelled} <= 1'}},
        'constraints',
        'c',
    )


@pytest.mark.parametrize(
    ('section', 'sugar', 'spelled'),
    [
        pytest.param(
            'variables',
            {'dims': ['active', 'connection']},
            {'dims': ['period', 'port', 'unit'], 'where': 'active AND connection'},
            id='a-variable',
        ),
        pytest.param(
            'variables',
            {'dims': ['active', 'site'], 'where': 'rating > 0'},
            {'dims': ['bus', 'period', 'unit'], 'where': '(active AND site) AND (rating > 0)'},
            id='a-variable-with-its-own-where',
        ),
        pytest.param(
            'variables',
            {'dims': ['connection', 'unit']},
            {'dims': ['port', 'unit'], 'where': 'connection'},
            id='a-tuple-beside-its-own-member',
        ),
        pytest.param(
            'parameters',
            {'dims': ['active', 'connection']},
            {'dims': ['period', 'port', 'unit'], 'where': 'active AND connection'},
            id='a-parameter',
        ),
    ],
)
def test_two_tuples_that_share_a_member_are_joined_on_it(section, sugar, spelled):
    """Was: refused, as an entry indexed by the shared member twice. The entry is over the members, at the rows both list."""
    built, meant = _program(**{f'{section}.e': sugar}), _program(**{f'{section}.e': spelled})
    entry, flat = getattr(built, section)['e'], getattr(meant, section)['e']
    assert entry.dims == flat.dims, 'the entry is over the members, each once'
    assert entry.where == flat.where, 'and confined to the rows both tuples list'


def test_a_parameter_over_two_tuples_refuses_a_row_outside_both():
    """The one change no flat spelling states: a tool refuses its data row outside the joined rows, where a `where:` drops it."""
    joined = _program(**{'parameters.e': {'dims': ['active', 'connection']}}).parameters['e']
    flat = _program(**{'parameters.e': {'dims': ['period', 'port', 'unit'], 'where': 'active AND connection'}})
    listed = And(RelationDefined('active', ('period', 'unit')), RelationDefined('connection', ('port', 'unit')))
    assert joined.domain == Mask(listed), 'the joined rows are the domain'
    assert flat.parameters['e'].domain is None, 'a where: is no domain: a tool drops a row outside it'


#: `output` over the tuples of `active`, and a ramp that steps along its ordered member.
_STEPPED = {
    'variables.output': {'dims': ['active']},
    'constraints.ramp_up': {
        'dims': ['active'],
        'expression': 'output - shift(output, along=period, offset=1) <= ramp',
    },
}

#: The same, over the members, as a dimension without an order must spell it.
_SPELLED = {
    'variables.output': {'dims': ['period', 'unit'], 'where': 'active'},
    'constraints.ramp_up': {
        'dims': ['period', 'unit'],
        'where': 'active',
        'expression': 'output - shift(output, along=period, offset=1) <= ramp',
    },
}


@pytest.mark.parametrize(('section', 'name'), [('variables', 'output'), ('constraints', 'ramp_up')])
def test_a_step_along_a_member_reads_the_entry_over_its_members(section, name):
    """Was: refused, as a step along a member of an entry over the tuple, with the flat entry as the rewrite."""
    _same(_STEPPED, _SPELLED, section, name)


def test_an_entry_over_the_tuple_reads_a_stepped_one_at_each_tuple():
    """`peak` stays over `active`, and reads `output`, which a step reads over its members, at each tuple."""
    peak = {'constraints.peak': {'dims': ['active'], 'expression': 'output <= ramp'}}
    spelled = 'at(output, by=active[period, unit]) <= at(ramp, by=active[unit])'
    flat = {'constraints.peak': {'dims': ['active'], 'expression': spelled}}
    _same(_STEPPED | peak, _SPELLED | flat, 'constraints', 'peak')


def test_an_entry_over_the_members_reads_a_tuple_at_them():
    """An entry over two tuples is over their members, and reads `flow`, over `connection`, at each pair of them."""
    limit = {'parameters.limit': {'dims': ['period', 'unit']}}
    sugar = {'dims': ['active', 'connection', 'snapshot'], 'expression': 'flow <= limit'}
    read = 'sum(flow, over=connection, by=connection[port, unit])'
    spelled = {
        'dims': ['period', 'port', 'snapshot', 'unit'],
        'where': 'active AND connection',
        'expression': f'{read} <= limit',
    }
    _same(limit | {'constraints.c': sugar}, limit | {'constraints.c': spelled}, 'constraints', 'c')


#: Each example this branch shortens, beside the spelling `compare/tuple-strict` writes.
STRICT = Path(__file__).parent / 'fixtures' / 'strict'
SHORTENED = sorted(path.relative_to(STRICT) for path in STRICT.rglob('*.yaml'))


@pytest.mark.parametrize('path', SHORTENED, ids=str)
def test_a_shortened_example_builds_the_program_of_its_strict_spelling(path):
    """Every #9 spelling keeps its meaning: the shorter file and the strict one build one program."""
    built, meant = to_spec(EXAMPLES / path).program, to_spec(STRICT / path).program
    domains = {n: p.domain for n, p in built.parameters.items() if p.domain is not None}
    assert not domains or set(domains) <= set(built.parameters), 'only a parameter carries a domain'
    stripped = {n: _without_domain(p) for n, p in built.parameters.items()}
    assert stripped == dict(meant.parameters), 'the parameters differ in their domain alone'
    for section in ('variables', 'constraints', 'expressions'):
        assert dict(getattr(built, section)) == dict(getattr(meant, section)), f'{section} are the strict ones'
    assert built.objective == meant.objective


def _without_domain(parameter):
    from dataclasses import replace

    return replace(parameter, domain=None)

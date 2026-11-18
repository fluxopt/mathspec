# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""A dimension that lists its members under `over:`: what loads, what it implies, and what is refused.

Its label is the tuple of its members, and it is one plain dimension in every
operator. Each member is a mapping of the dimension, read as `dimension[member]`.
"""

from __future__ import annotations

from typing import Any

import pytest

from mathspec import merge, override, rename, to_spec
from mathspec._advising import advice
from mathspec._typesetting import FORMATS, typeset
from mathspec.errors import LanguageError
from mathspec.program import JoinedCondition, Relation, RelationComparison, RelationDefined
from tests.fixtures import varied

#: The example of #1011: `connection` lists (unit, port) pairs and maps each to a
#: bus, `trade` lists a region and its alias, and `active` is a sparse set with an
#: ordered member.
MODEL: dict[str, Any] = {
    'dimensions': {
        'unit': {},
        'port': {},
        'bus': {},
        'region': {},
        'from_region': {'alias': 'region'},
        'snapshot': {'dtype': 'int', 'ordered': True},
        'period': {'dtype': 'int', 'ordered': True},
        'connection': {'over': ['unit', 'port']},
        'trade': {'over': ['from_region', 'region']},
        'active': {'over': ['unit', 'period']},
    },
    'mappings': {'connection': {'bus': {'dim': 'bus'}}},
    'parameters': {
        'capacity': {'dims': ['unit']},
        'rating': {'dims': ['unit', 'port']},
        'tariff': {'dims': ['region']},
        'load': {'dims': ['bus', 'snapshot']},
    },
    'variables': {
        'flow': {'dims': ['connection', 'snapshot'], 'bounds': {'lower': 0}},
        'shipped': {'dims': ['trade'], 'bounds': {'lower': 0}},
    },
    'constraints': {
        'limit': {'dims': ['connection', 'snapshot'], 'expression': 'flow <= at(capacity, by=connection[unit])'},
        'balance': {
            'dims': ['bus', 'snapshot'],
            'expression': 'sum(flow, over=connection, by=connection[bus]) == load',
        },
    },
}


FRAGMENT: dict[str, Any] = {
    'dimensions': {'unit': {}, 'port': {}, 'connection': {'over': ['unit', 'port']}},
    'variables': {'flow': {'dims': ['connection']}},
}


def _refusal(**patch: Any) -> str:
    """The message `to_spec` refuses the model patched with, and it has to refuse."""
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(MODEL, **patch))
    return str(caught.value)


def _constraint(expression: str, dims: list[str]) -> dict[str, Any]:
    return {'constraints.probe': {'dims': dims, 'expression': expression}}


def test_each_member_is_a_map_of_the_dimension():
    program = to_spec(MODEL).program
    connection = program.dimensions['connection']
    assert connection.over == (('port', 'port'), ('unit', 'unit')), 'members are (role, dimension), sorted by role'
    assert connection.missing == 'absent', 'a tuple dimension is a sparse subset unless the file says refused'
    assert program.relations['connection'] == Relation(
        (('connection', 'connection'), ('bus', 'bus'), ('port', 'port'), ('unit', 'unit')),
        ('connection',),
        'refused',
        members=('port', 'unit'),
    ), 'the table of the dimension has a mapping per member beside the mappings the file declares'
    assert program.relations['trade'].members == ('from_region', 'region'), (
        'a dimension with no declared mapping has its members'
    )
    assert program.dimensions['trade'].over == (('from_region', 'from_region'), ('region', 'region')), (
        'a member is named after its dimension, an alias where the tuple holds one dimension twice'
    )
    assert program.dimensions['unit'].over == (), 'a plain dimension has no members'


def test_the_order_of_the_members_changes_nothing():
    swapped = varied(MODEL, **{'dimensions.connection': {'over': ['port', 'unit']}})
    assert to_spec(swapped) == to_spec(MODEL)


@pytest.mark.parametrize('missing', ['absent', 'refused'])
def test_missing_says_whether_the_full_product_is_required(missing):
    spec = to_spec(varied(MODEL, **{'dimensions.connection.missing': missing}))
    assert spec.program.dimensions['connection'].missing == missing
    assert spec.program.relations['connection'].missing == 'refused', 'every tuple has its members, either way'
    assert spec.program.relations['connection'].partial == (), 'no member may leave a tuple without a label'


@pytest.mark.parametrize(
    ('expression', 'dims'),
    [
        pytest.param('flow <= at(capacity, by=connection[unit])', ['connection', 'snapshot'], id='one-member'),
        pytest.param('flow <= at(rating, by=connection[unit, port])', ['connection', 'snapshot'], id='every-member'),
        pytest.param('shipped <= at(tariff, by=trade[region])', ['trade'], id='a-member-beside-its-alias'),
        pytest.param(
            'sum(flow, over=connection, by=connection[port]) >= 0', ['port', 'snapshot'], id='sum-to-a-member'
        ),
        pytest.param('sum(flow, over=connection) >= 0', ['snapshot'], id='sum-the-tuples-away'),
    ],
)
def test_a_member_is_read_as_a_map_of_the_dimension(expression, dims):
    constraint = to_spec(varied(MODEL, **_constraint(expression, dims))).program.constraints['probe']
    assert sorted({*constraint.lhs.dims, *constraint.rhs.dims}) == sorted(dims)


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param(_constraint('flow <= capacity', ['connection', 'unit', 'snapshot']), id='a-constraint'),
        pytest.param(
            {'expressions.e': {'dims': ['connection', 'unit', 'snapshot'], 'expression': 'flow * capacity'}},
            id='a-named-expression',
        ),
        pytest.param(
            _constraint('sum(flow * capacity, over=snapshot) <= 1', ['connection', 'unit']),
            id='under-a-sum-that-keeps-both',
        ),
        pytest.param(
            {
                'variables.both': {
                    'dims': ['connection', 'unit'],
                    'where': 'at(rating, by=connection[unit, port]) > capacity',
                }
            },
            id='a-condition',
        ),
        pytest.param(
            {
                'constraints.probe': {
                    'dims': ['connection', 'unit'],
                    'expression': 'at(rating, by=connection[unit, port]) <= capacity',
                    'where': 'at(rating, by=connection[unit, port]) > capacity',
                }
            },
            id='a-constraint-where',
        ),
        pytest.param(
            {
                'parameters.p': {
                    'dims': ['connection', 'unit'],
                    'where': 'at(rating, by=connection[unit, port]) > capacity',
                }
            },
            id='a-parameter-where',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['connection', 'unit', 'snapshot'],
                    'cases': {
                        'a': {
                            'when': 'at(rating, by=connection[unit, port]) > capacity',
                            'expression': 'flow * capacity',
                        }
                    },
                    'otherwise': 'flow * capacity',
                }
            },
            id='a-case',
        ),
        pytest.param(
            {
                'parameters.xs': {'dims': ['period']},
                'parameters.ys': {'dims': ['period']},
                'variables.w': {'dims': ['connection']},
                'variables.v': {'dims': ['unit']},
                'variables.y': {'dims': ['connection', 'unit']},
                'piecewise.curve': {
                    'dims': ['connection', 'unit'],
                    'along': 'period',
                    'links': {'x': ['w + v', 'xs'], 'y': ['y', 'ys']},
                },
            },
            id='a-piecewise-link',
        ),
    ],
)
def test_a_frame_over_the_dimension_and_its_member_is_refused(patch):
    """Rule 11 of #1011 read these as the cross product; a later reading by member name would read them as a join."""
    assert "'connection' and 'unit' in dims: share the member 'unit'" in _refusal(**patch)


_SPAN = {'dimensions.span': {'over': ['unit', 'period']}}


@pytest.mark.parametrize(
    ('patch', 'read'),
    [
        pytest.param(
            {'variables.built': {'dims': ['unit', 'period'], 'where': 'span'}},
            lambda spec: spec.program.variables['built'].where,
            id='a-variable-where',
        ),
        pytest.param(
            {'parameters.cost': {'dims': ['period', 'unit'], 'where': 'span'}},
            lambda spec: spec.program.parameters['cost'].where,
            id='a-parameter-where',
        ),
        pytest.param(
            {
                'variables.built': {'dims': ['unit', 'period']},
                'constraints.probe': {'dims': ['unit', 'period'], 'expression': 'built >= 0', 'where': 'span'},
            },
            lambda spec: spec.program.constraints['probe'].where,
            id='a-constraint-where',
        ),
        pytest.param(
            {'conditions.on': 'span', 'variables.built': {'dims': ['unit', 'period'], 'where': 'on'}},
            lambda spec: spec.program.variables['built'].where,
            id='a-named-condition',
        ),
    ],
)
def test_a_tuple_dimension_tests_membership_on_an_entry_over_every_member(patch, read):
    """The bare name keeps the rows whose member labels the dimension lists; it aligns nothing by name."""
    spec = to_spec(varied(MODEL, **_SPAN, **patch))
    assert read(spec).atoms == (RelationDefined('span', ('period', 'unit')),), 'a test of the member tuple'


@pytest.mark.parametrize(
    ('fmt', 'printed'),
    [
        pytest.param('latex', r'\left( p,\ u \right) \in \mathrm{span}', id='latex'),
        pytest.param('markdown', r'\left( p,\ u \right) \in \mathrm{span}', id='markdown'),
        pytest.param('typst', 'colon (p, u) in upright("span")', id='typst'),
    ],
)
def test_a_membership_test_prints_the_member_indices(fmt, printed):
    """It prints the tuple of the frame's member indices, not an index of the dimension."""
    patch = {'variables.built': {'dims': ['unit', 'period'], 'where': 'span'}}
    assert printed in typeset(to_spec(varied(MODEL, **_SPAN, **patch)), fmt)


def test_a_tuple_dimension_tests_membership_in_a_case():
    case = {'when': 'span', 'expression': 'capacity'}
    named = {'dims': ['unit', 'period'], 'cases': {'on': case}, 'otherwise': '0'}
    spec = to_spec(varied(MODEL, **_SPAN, **{'expressions.e': named}))
    expression = repr(spec.program.expressions['e'].expression)
    assert repr(RelationDefined('span', ('period', 'unit'))) in expression, 'the case tests the member tuple'


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param({'variables.built': {'dims': ['unit'], 'where': 'span'}}, id='a-member-missing'),
        pytest.param({'variables.built': {'dims': ['span'], 'where': 'span'}}, id='over-the-dimension-itself'),
        pytest.param({'variables.built': {'dims': ['unit', 'snapshot'], 'where': 'span'}}, id='a-member-replaced'),
    ],
)
def test_a_tuple_dimension_tests_membership_only_where_the_entry_has_every_member(patch):
    message = _refusal(**_SPAN, **patch)
    assert "where-tuple 'span' reads dims" in message, message
    assert 'outside the declared dims' in message


_STEPPED = {'dimensions.span': {'over': ['unit', 'period']}, 'variables.out': {'dims': ['span']}}


@pytest.mark.parametrize(
    'patch',
    [
        pytest.param(_constraint('out - shift(out, along=period, offset=1) <= 1', ['span']), id='shift'),
        pytest.param(_constraint('sum_back(out, along=period, window=2) <= 1', ['span']), id='sum-back'),
        pytest.param(
            {'constraints.probe': {'dims': ['span'], 'where': 'position(period) > 0', 'expression': 'out <= 1'}},
            id='position',
        ),
    ],
)
def test_a_step_along_a_member_of_an_entry_over_the_tuple_names_the_flat_entry(patch):
    """The entry is over the tuple, which has no order, so the rewrite is the entry over the members, confined by the tuple."""
    message = _refusal(**_STEPPED, **patch)
    assert "'period' is a member of 'span'" in message, message
    assert "dims: ['period', 'unit'], with where: span" in message, message


def test_a_condition_compares_a_member_label():
    spec = to_spec(varied(MODEL, **{'variables.flow.where': "connection[unit] == 'gas'"}))
    (atom,) = spec.program.variables['flow'].where.atoms
    assert atom == RelationComparison('connection', 'unit', '==', 'gas', ('connection',))


def test_a_sparse_set_with_an_ordered_member_is_read_at_a_tuple():
    """Rule 9 of #1011: `active` is a tuple with an ordered member, and an entry over `connection` reads it with `at`."""
    built = {'dims': ['connection', 'period'], 'where': 'at(active, by=connection[unit])'}
    spec = to_spec(varied(MODEL, **{'variables.built': built}))
    (atom,) = spec.program.variables['built'].where.atoms
    assert isinstance(atom, JoinedCondition)
    assert spec.program.variables['built'].where.dims == ('connection', 'period')


@pytest.mark.parametrize(
    ('patch', 'fragments'),
    [
        pytest.param(
            {'dimensions.pair': {'over': ['connection', 'bus']}},
            (
                "Dimension 'pair' lists 'connection' under 'over:', and 'connection' has members of its own",
                "over: ['bus', 'port', 'unit']",
            ),
            id='a-tuple-dimension-as-a-member',
        ),
        pytest.param(
            {'dimensions.pair': {'over': ['unit', 'nope']}},
            ("Dimension 'pair' references undeclared dimension 'nope'",),
            id='an-undeclared-member',
        ),
        pytest.param(
            {'dimensions.connection.ordered': True},
            ('dimensions.connection', '`ordered: true`', 'no order', "over ['port', 'unit']", 'where:'),
            id='ordered',
        ),
        pytest.param(
            {'dimensions.connection.one_of': ['a']},
            ('dimensions.connection', '`one_of:`', 'the label is the tuple of its members', 'one_of: of a member'),
            id='one-of',
        ),
        pytest.param(
            {'dimensions.connection.dtype': 'str'},
            ('dimensions.connection', '`dtype:`', 'the label is the tuple of its members', 'dtype: of a member'),
            id='dtype',
        ),
        pytest.param(
            {'dimensions.bus.missing': 'refused'},
            ('dimensions.bus', '`missing:`', 'without `over:`', 'Delete `missing:`'),
            id='missing-without-members',
        ),
        pytest.param(
            {'dimensions.connection.missing': 0},
            ('missing: 0 on a dimension', 'takes absent or refused'),
            id='missing-is-a-number',
        ),
        pytest.param(
            {'dimensions.connection.over': []},
            ('dimensions.connection.over', 'lists no member', 'leave `over:` out'),
            id='no-member',
        ),
        pytest.param(
            {'dimensions.pair': {'over': ['region', 'region']}},
            ("Dimension 'pair' lists 'region' twice under 'over:'", "Declare an alias of 'region'"),
            id='a-dimension-twice',
        ),
        pytest.param(
            {'mappings.connection.unit': {'dim': 'unit'}},
            ("mappings: 'connection': mapping 'unit' has the name of a member of 'connection'", 'connection[unit]'),
            id='a-declared-mapping-named-after-a-member',
        ),
        pytest.param(
            _constraint("shift(flow, along=connection, offset=1, edge='wrap') >= 0", ['connection', 'snapshot']),
            ("shift(along=connection) reads the order of 'connection'", 'no order', "over ['port', 'unit']"),
            id='shift',
        ),
        pytest.param(
            _constraint('sum_back(flow, along=connection, window=2) >= 0', ['connection', 'snapshot']),
            ("sum_back(along=connection) reads the order of 'connection'", 'no order'),
            id='sum-back',
        ),
        pytest.param(
            {'variables.flow.where': 'position(connection) == 0'},
            ("position(connection) reads the order of 'connection'", 'no order'),
            id='position',
        ),
        pytest.param(
            {
                'parameters.xs': {'dims': ['connection']},
                'parameters.ys': {'dims': ['connection']},
                'variables.x': {'dims': []},
                'variables.y': {'dims': []},
                'piecewise.curve': {'dims': [], 'along': 'connection', 'links': {'x': ['x', 'xs'], 'y': ['y', 'ys']}},
            },
            ("piecewise 'curve': along: connection reads the order of 'connection'", 'no order'),
            id='piecewise',
        ),
        pytest.param(
            {
                'variables.flow.bounds.upper': 1,
                'sos.pick': {'variable': 'flow', 'along': 'connection', 'type': 2},
            },
            ("Sos 'pick': type: 2 along connection reads the order of 'connection'", "over ['port', 'unit']"),
            id='sos-of-type-2',
        ),
        pytest.param(
            {'variables.both': {'dims': ['connection', 'unit']}}
            | _constraint('at(both, by=connection[unit]) >= 0', ['connection']),
            (
                "Variable 'both': 'connection' and 'unit' in dims: share the member 'unit'",
                'read it as connection[unit]',
            ),
            id='an-operand-with-the-tuple-and-a-member',
        ),
        pytest.param(
            _constraint('sum(flow, over=unit) >= 0', ['connection', 'snapshot']),
            (
                "'unit' is a member of 'connection'",
                'sum(..., over=connection, by=connection[port])',
            ),
            id='over-names-a-member',
        ),
        pytest.param(
            _constraint('sum(flow, over=unit, by=connection[port]) >= 0', ['port', 'snapshot']),
            ("over=unit names a member of 'connection'", 'sum(..., over=connection, by=connection[port])'),
            id='over-names-a-member-beside-by',
        ),
        pytest.param(
            _constraint('sum(flow, over=unit, by=connection[bus]) >= 0', ['bus', 'snapshot']),
            ("over=unit names a member of 'connection'", 'sum(..., over=connection, by=connection[bus])'),
            id='over-names-a-member-beside-a-declared-mapping',
        ),
        pytest.param(
            _constraint('sum(flow, over=[unit, port]) >= 0', ['snapshot']),
            ("'unit' is a member of 'connection'", 'Write sum(..., over=connection).'),
            id='over-names-every-member',
        ),
        pytest.param(
            _constraint('sum(shipped, over=region) >= 0', ['trade']),
            ("'region' is a member of 'trade'", 'Write sum(..., over=trade, by=trade[from_region]).'),
            id='over-names-a-member-beside-its-alias',
        ),
        pytest.param(
            _constraint('flow <= capacity', ['connection', 'snapshot']),
            (
                "an operand over ['unit'] meets one over 'connection'",
                'at(capacity, by=connection[unit])',
                'sum(flow, over=connection, by=connection[unit])',
            ),
            id='a-member-operand-meets-the-tuple',
        ),
        pytest.param(
            _constraint('flow <= capacity', ['unit', 'snapshot']),
            ("meets one over 'connection'", 'sum(flow, over=connection, by=connection[unit])'),
            id='a-member-operand-meets-the-tuple-in-a-frame-over-the-member',
        ),
        pytest.param(
            {'objective': {'sense': 'minimize', 'expression': 'sum(flow * capacity)'}},
            (
                "The objective: an operand over ['unit'] meets one over 'connection'",
                'at(capacity, by=connection[unit])',
            ),
            id='a-member-operand-meets-the-tuple-in-a-product',
        ),
        pytest.param(
            _constraint('sum(flow * capacity, over=unit) <= 1', ['connection', 'snapshot']),
            ("meets one over 'connection'", 'at(capacity, by=connection[unit])'),
            id='a-member-operand-meets-the-tuple-under-a-sum',
        ),
        pytest.param(
            _constraint('sum(flow * capacity, over=unit) <= 1', ['connection', 'unit', 'snapshot']),
            ("Constraint 'probe': 'connection' and 'unit' in dims: share the member 'unit'",),
            id='a-member-operand-meets-the-tuple-under-a-sum-over-the-member-the-frame-declares',
        ),
        pytest.param(
            _constraint('sum(flow * capacity) <= 1', ['connection', 'snapshot']),
            ("meets one over 'connection'", 'at(capacity, by=connection[unit])'),
            id='a-member-operand-meets-the-tuple-under-a-sum-over-everything',
        ),
        pytest.param(
            {'assumptions.a': 'at(rating, by=connection[unit, port]) > capacity'},
            ("Assumption 'a': an operand over ['unit'] meets one over 'connection'",),
            id='a-member-operand-meets-the-tuple-in-an-assumption',
        ),
        pytest.param(
            {
                'parameters.xs': {'dims': ['period']},
                'parameters.ys': {'dims': ['period']},
                'variables.y': {'dims': ['connection']},
                'piecewise.curve': {
                    'dims': ['connection'],
                    'along': 'period',
                    'links': {'x': ['y', 'xs'], 'y': ['y', 'ys']},
                    'where': 'at(rating, by=connection[unit, port]) > capacity',
                },
            },
            ("piecewise 'curve' where: an operand over ['unit'] meets one over 'connection'",),
            id='a-member-operand-meets-the-tuple-in-a-piecewise-where-its-assumptions-repeat',
        ),
        pytest.param(
            {'variables.flow.where': 'at(rating, by=connection[unit, port]) > capacity'},
            ("Variable 'flow': an operand over ['unit'] meets one over 'connection'",),
            id='a-member-operand-meets-the-tuple-in-a-condition',
        ),
        pytest.param(
            {'expressions.e': {'dims': ['unit'], 'expression': '2 * capacity'}}
            | _constraint('flow <= e', ['connection', 'snapshot']),
            ('at(e, by=connection[unit])',),
            id='a-named-expression-over-a-member-meets-the-tuple',
        ),
        pytest.param(
            {'expressions.e': {'dims': ['connection', 'snapshot'], 'expression': 'capacity'}},
            ("the body carries dims ['unit']", 'at(capacity, by=connection[unit])'),
            id='a-named-expression-body-over-a-member',
        ),
        pytest.param(
            {
                'expressions.e': {
                    'dims': ['connection', 'snapshot'],
                    'cases': {'a': {'when': "connection[unit] == 'u'", 'expression': 'capacity'}},
                    'otherwise': 'flow',
                }
            },
            ("the value carries dims ['unit']", 'at(capacity, by=connection[unit])'),
            id='a-case-value-over-a-member',
        ),
        pytest.param(
            {'variables.u': {'dims': ['unit']}} | _constraint('sum(u, over=unit, by=connection[port]) >= 0', ['port']),
            ('sum(at(u, by=connection[unit]), over=connection, by=connection[port])',),
            id='over-names-a-member-of-an-operand-without-the-dimension',
        ),
        pytest.param(
            {'variables.u': {'dims': ['unit']}} | _constraint('u <= 1', ['connection']),
            ("carries dims ['unit'] that are not in its dims", 'at(u, by=connection[unit])'),
            id='a-constraint-over-a-member-its-dims-lack',
        ),
        pytest.param(
            {'variables.flow.bounds.upper': 'capacity'},
            (
                "parameter 'capacity' has dims ['unit'] outside",
                'Bound the variable in a constraint',
                'flow <= at(capacity, by=connection[unit])',
            ),
            id='a-bound-over-a-member',
        ),
        pytest.param(
            {'variables.flow.where': 'capacity > 0'},
            ("reads dims ['unit'] outside the declared dims", 'at(capacity, by=connection[unit])'),
            id='a-where-over-a-member',
        ),
        pytest.param(
            {'variables.flow.where': "connection == 'a'"},
            ("'connection' lists its members", 'no label to compare', "connection[port] == 'a'"),
            id='a-label-comparison',
        ),
        pytest.param(
            {'variables.flow.where': 'connection'},
            ("where-tuple 'connection' reads dims ['port', 'unit'] outside the declared dims",),
            id='a-bare-dimension-with-members',
        ),
        pytest.param(
            {'dimensions.ring': {'over': ['loop', 'unit']}, 'dimensions.loop': {'over': ['ring', 'port']}},
            ("Dimension 'ring' lists 'loop'", "over: ['port', 'unit']"),
            id='two-dimensions-as-members-of-each-other',
        ),
    ],
)
def test_what_a_tuple_dimension_does_not_take_is_refused_with_the_rewrite(patch, fragments):
    message = _refusal(**patch)
    for fragment in fragments:
        assert fragment in message


def test_no_advice_about_a_tuple_dimension_where_none_is_in_play():
    """A stray dimension that is no member keeps the advice it had."""
    message = _refusal(**_constraint('flow <= load', ['connection', 'snapshot']))
    assert 'Add them to dims:, or sum them out' in message
    assert 'at(' not in message, 'bus is no member of connection'


@pytest.mark.parametrize('fmt', FORMATS)
@pytest.mark.parametrize(
    ('missing', 'relation'),
    [pytest.param('absent', 'subset_of', id='a-subset'), pytest.param('refused', 'equal', id='the-full-product')],
)
def test_the_legend_prints_the_members(fmt, missing, relation):
    spec = to_spec(varied(FRAGMENT, **{'dimensions.connection.missing': missing}))
    ops = FORMATS[fmt].operators
    c, p, u = ((r'cal(%s)' if fmt == 'typst' else r'\mathcal{%s}') % letter for letter in 'CPU')
    assert f'{c} {ops[relation]} {p} {ops["times"]} {u}' in typeset(spec, fmt), f'{fmt} prints the product'
    member = r'upright("unit")' if fmt == 'typst' else r'\mathrm{unit}'
    assert member not in typeset(spec, fmt), 'a member prints as the product, not as a mapping of its own'


def test_a_set_of_type_1_runs_along_a_dimension_with_members():
    """A type-1 set uses no order, so a dimension without one carries it."""
    sos = {'variables.flow.bounds.upper': 1, 'sos.pick': {'variable': 'flow', 'along': 'connection', 'type': 1}}
    assert to_spec(varied(MODEL, **sos)).sos['pick'].along == 'connection'


@pytest.mark.parametrize(
    ('variables', 'unused'),
    [
        pytest.param({'x': {'dims': ['snapshot']}}, ['connection', 'port', 'unit'], id='nothing-is-over-the-dimension'),
        pytest.param({'x': {'dims': ['connection']}}, ['snapshot'], id='an-entry-is-over-the-dimension'),
        pytest.param(
            {'x': {'dims': ['port', 'unit'], 'where': 'connection'}}, ['snapshot'], id='a-where-tests-the-dimension'
        ),
    ],
)
def test_a_member_does_not_count_as_a_use(variables, unused):
    """The table of the dimension has a column over the dimension and each member, so it counted as reaching them."""
    spec = {
        'dimensions': {'unit': {}, 'port': {}, 'snapshot': {}, 'connection': {'over': ['unit', 'port']}},
        'variables': variables,
    }
    notes = sorted(note.subject for note in advice(spec) if note.kind == 'never-an-axis')
    assert notes == unused, 'an entry over the dimension reaches its members, and a member reaches nothing'


def test_fragments_that_agree_on_the_members_merge():
    other = {
        'dimensions': {'port': {}, 'unit': {}, 'connection': {'over': ['port', 'unit']}},
        'variables': {'loss': {'dims': ['connection']}},
    }
    assert merge([FRAGMENT, other]).program.dimensions['connection'].over == (('port', 'port'), ('unit', 'unit'))


@pytest.mark.parametrize(
    'connection',
    [
        pytest.param({'over': ['unit']}, id='other-members'),
        pytest.param({'over': ['unit', 'port'], 'missing': 'refused'}, id='other-missing'),
        pytest.param({}, id='no-members'),
    ],
)
def test_fragments_that_disagree_on_the_members_are_refused(connection):
    other = {
        'dimensions': {'port': {}, 'unit': {}, 'connection': connection},
        'variables': {'loss': {'dims': ['connection']}},
    }
    with pytest.raises(LanguageError, match=r"say different things about the dimension 'connection'") as raised:
        merge([FRAGMENT, other])
    assert 'Make the two identical' in str(raised.value)


def test_a_patch_cannot_change_the_members():
    with pytest.raises(LanguageError, match=r"declares the dimension 'connection'"):
        override(FRAGMENT, [{'dimensions': {'connection': {'over': ['unit']}}}])


def test_rename_reaches_the_members_and_their_reads():
    renamed = rename(MODEL, {'unit': 'plant', 'connection': 'link', 'region': 'zone'})
    assert renamed.dimensions['link'].over == ('plant', 'port')
    assert set(renamed.dimensions['trade'].over) == {'from_region', 'zone'}, 'a member follows its dimension'
    assert renamed.constraints['limit'].expression == 'flow <= at(capacity, by=link[plant])'
    assert rename(renamed, {'plant': 'unit', 'link': 'connection', 'zone': 'region'}) == to_spec(MODEL)


@pytest.mark.parametrize('canonical', [False, True])
def test_a_spec_with_members_is_written_and_read_back(canonical):
    spec = to_spec(MODEL)
    assert to_spec(spec.to_yaml(canonical=canonical)).program == spec.program

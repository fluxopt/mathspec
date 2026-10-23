# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`subject[property]` in a call and in a condition: the table it reads, and every refusal decided at load."""

from __future__ import annotations

from typing import Any

import pytest

from mathspec import to_spec
from mathspec._typesetting import FORMATS, typeset
from mathspec.errors import LanguageError
from mathspec.program import (
    And,
    Join,
    Not,
    Relation,
    RelationComparison,
    RelationDefined,
    RelationPairComparison,
    Sum,
    Translate,
    walk,
)
from tests.fixtures import varied
from tests.test_sets import MODEL

CALLS: dict[str, Any] = varied(
    MODEL,
    **{
        'dimensions.carrier': {},
        'dimensions.season': {},
        'properties.generator.carrier': {'into': 'carrier', 'missing': 'absent'},
        'properties.snapshot.season': 'season',
        'parameters.cap': {'dims': ['bus', 'carrier']},
        'parameters.price': {'dims': ['zone', 'period']},
        'parameters.load': {'dims': ['bus', 'snapshot']},
        'variables.x': {'dims': ['generator', 'snapshot']},
        'variables.f': {'dims': ['line', 'snapshot']},
    },
)


def _expression(text: str) -> Any:
    return to_spec(varied(CALLS, **{'expressions.e': text})).program.expressions['e'].expression


def _where(variable: str, text: str) -> Any:
    where = to_spec(varied(CALLS, **{f'variables.{variable}.where': text})).program.variables[variable].where
    assert where is not None
    return where


def _refusal(**patch: Any) -> str:
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(CALLS, **patch))
    return str(caught.value)


@pytest.mark.parametrize(
    ('text', 'dims', 'name', 'tables'),
    [
        pytest.param(
            'sum(x, over=generator, by=generator[bus])',
            ('bus', 'snapshot'),
            'generator.bus',
            ('generator.bus',),
            id='a-sum-grouped-by-a-property',
        ),
        pytest.param(
            'sum(x, over=generator, by=generator[bus, carrier])',
            ('bus', 'carrier', 'snapshot'),
            'generator',
            ('generator.bus', 'generator.carrier'),
            id='a-sum-grouped-by-two-properties',
        ),
        pytest.param(
            'at(cap, by=generator[bus, carrier])',
            ('generator',),
            'generator',
            ('generator.bus', 'generator.carrier'),
            id='a-lookup-at-two-properties',
        ),
        pytest.param(
            'at(price, by=generator_period[zone])',
            ('generator', 'period'),
            'generator_period.zone',
            ('generator_period.zone',),
            id='a-lookup-at-a-property-of-a-set',
        ),
        pytest.param(
            'sum(eff * inj, over=[entity, port], by=connection[bus])',
            ('bus', 'snapshot'),
            'connection.bus',
            ('connection.bus',),
            id='a-sum-over-the-members-of-a-set-grouped-by-its-property',
        ),
        pytest.param(
            'sum(x, over=start, by=cover[covered])',
            ('generator', 'snapshot'),
            'cover',
            ('cover',),
            id='a-sum-through-the-members-of-a-set',
        ),
    ],
)
def test_a_call_reads_the_table_of_what_it_names(text, dims, name, tables):
    expression = _expression(text)
    (join,) = [node for node in walk(expression) if isinstance(node, Join)]
    assert expression.dims == dims
    assert join.columns.name == name
    assert join.columns.tables == tables


@pytest.mark.parametrize(
    ('text', 'tables'),
    [
        pytest.param('shift(x, along=snapshot, offset=1, within=snapshot[period])', ('snapshot.period',), id='one'),
        pytest.param(
            'shift(x, along=snapshot, offset=1, within=snapshot[period, season])',
            ('snapshot.period', 'snapshot.season'),
            id='two',
        ),
    ],
)
def test_a_partition_reads_the_tables_of_the_properties_it_names(text, tables):
    expression = _expression(text)
    assert isinstance(expression, Translate)
    assert expression.partition is not None
    assert expression.partition.tables == tables


def test_several_properties_are_read_as_their_inner_join():
    """A row of the join is a generator with every property named; one it lacks is no row, so its missing is absent."""
    (join,) = [node for node in walk(_expression('at(cap, by=generator[bus, carrier])')) if isinstance(node, Join)]
    assert join.columns.relation == Relation(
        (('generator', 'generator'), ('bus', 'bus'), ('carrier', 'carrier')),
        ('generator',),
        'absent',
        subject='generator',
    )


def test_a_sum_through_two_properties_sums_each_group_once():
    sum_ = _expression('sum(x, over=generator, by=generator[bus, carrier])')
    assert isinstance(sum_, Sum)
    assert [type(node).__name__ for node in walk(sum_)][:2] == ['Sum', 'Join'], 'one join, then one sum'


@pytest.mark.parametrize(
    ('variable', 'text', 'root'),
    [
        pytest.param('f', 'line[bus1]', RelationDefined('line.bus1', ('line',)), id='has-a-property'),
        pytest.param(
            'x',
            'generator[bus, carrier]',
            And(RelationDefined('generator.bus', ('generator',)), RelationDefined('generator.carrier', ('generator',))),
            id='has-two-properties',
        ),
        pytest.param('f', 'not line[bus1]', Not(RelationDefined('line.bus1', ('line',))), id='lacks-a-property'),
        pytest.param(
            'x',
            "generator[bus] == 'b1'",
            RelationComparison('generator.bus', 'bus', '==', 'b1', ('generator',)),
            id='compares-a-property',
        ),
        pytest.param(
            'inj',
            "connection[bus] == 'b1'",
            RelationComparison('connection.bus', 'bus', '==', 'b1', ('entity', 'port')),
            id='compares-a-property-of-a-set',
        ),
        pytest.param(
            'f',
            'line[bus0] != line[bus1]',
            RelationPairComparison('line.bus0', 'bus0', 'line.bus1', 'bus1', '!=', ('line',)),
            id='compares-two-properties',
        ),
    ],
)
def test_a_condition_reads_a_property(variable, text, root):
    assert _where(variable, text).root == root


def test_a_mask_through_two_properties_reads_both_tables():
    where = _where('x', 'at(cap > 0, by=generator[bus, carrier])')
    assert where.names_read == {'cap', 'generator.bus', 'generator.carrier'}, (
        'the data supplies each property as a table, and no table named after the subject'
    )


def test_a_position_within_a_property_reads_its_table():
    where = _where('x', 'position(snapshot, within=snapshot[period]) == 0')
    assert where.root.partition is not None
    assert where.root.partition.name == 'snapshot.period'


@pytest.mark.parametrize(
    ('patch', 'fragment'),
    [
        pytest.param(
            {'expressions.e': 'sum(x, over=generator, by=generator[generator])'},
            "sum(by=generator[generator]) reads no property of 'generator', and a dimension has no table of its "
            "own. Name one of its properties, ['bus', 'carrier'].",
            id='a-dimension-read-by-its-own-name',
        ),
        pytest.param(
            {'expressions.e': 'sum(x, over=generator, by=generator[zone])'},
            "sum(by=generator[zone]) names ['zone'], which is no property of 'generator'. Name one of its "
            "properties, ['bus', 'carrier'].",
            id='a-property-the-dimension-lacks',
        ),
        pytest.param(
            {'expressions.e': 'sum(eff, over=entity, by=connection[zone])'},
            "sum(by=connection[zone]) names ['zone'], which is no member or property of 'connection'. Name one "
            "of its members and properties, ['entity', 'port', 'bus'].",
            id='a-property-the-set-lacks',
        ),
        pytest.param(
            {'expressions.e': 'sum(load, over=bus, by=bus[zone])'},
            "sum(by=bus[...]): 'bus' is a dimension with no properties. Declare one under properties: "
            'bus: {<property>: <dimension>}',
            id='a-dimension-with-no-properties',
        ),
        pytest.param(
            {'expressions.e': 'at(x, by=generator[bus])'},
            "at(by=generator[bus]) joins on ['bus'], which the expression does not carry",
            id='a-lookup-at-a-dimension-the-operand-lacks',
        ),
        pytest.param(
            {'variables.x.where': 'generator[zone]'},
            "'generator[zone]' names ['zone'], which is no property of 'generator'. Properties: bus, carrier.",
            id='a-presence-test-of-a-property-the-dimension-lacks',
        ),
        pytest.param(
            {'variables.x.where': 'nowhere[bus]'},
            "Variable 'x': 'nowhere' not found.",
            id='a-presence-test-of-an-undeclared-name',
        ),
        pytest.param(
            {'variables.x.where': 'cap[bus]'},
            "'cap[bus]' reads a column of 'cap', which is a parameter. Only a relation, a set or a dimension has "
            'columns.',
            id='a-presence-test-of-a-parameter',
        ),
        pytest.param(
            {'variables.inj.where': 'connection[port]'},
            "'connection[port]' alone tests no property of 'connection'. Test whether 'connection' has a row with "
            "its bare name, 'connection'.",
            id='a-presence-test-of-a-member',
        ),
        pytest.param(
            {'variables.x.where': "generator[zone] == 'z'"},
            "'generator[zone]' reads 'zone', which is no property of 'generator'. Properties: bus, carrier.",
            id='a-comparison-of-a-property-the-dimension-lacks',
        ),
        pytest.param(
            {'variables.f.where': 'line[bus0] != line[bus9]'},
            "'line[bus9]' reads 'bus9', which is no property of 'line'. Did you mean 'bus1'?",
            id='a-pair-with-a-property-the-dimension-lacks',
        ),
        pytest.param(
            {'variables.x.where': "generator[bus, carrier] == 'b1'"},
            "a comparison reads one column of 'generator'. Compare each column on its own: generator[bus] == … "
            'AND generator[carrier] == ….',
            id='a-comparison-of-two-properties',
        ),
        pytest.param(
            {'variables.x.where': "x[bus] == 'b1'"},
            "'x[bus]' reads a column of 'x', which is a variable. Only a relation, a set or a dimension has columns.",
            id='a-column-of-a-variable',
        ),
    ],
)
def test_a_property_read_the_language_refuses(patch, fragment):
    assert fragment in _refusal(**patch)


@pytest.mark.parametrize('fmt', FORMATS)
def test_the_typesetter_prints_a_read_of_several_properties(fmt):
    spec = varied(
        CALLS,
        **{
            'variables.x.where': 'generator[bus, carrier]',
            'constraints.c': {
                'dims': ['bus', 'carrier', 'snapshot'],
                'expression': 'sum(x, over=generator, by=generator[bus, carrier]) <= cap',
            },
        },
    )
    printed = typeset(spec, fmt)
    assert 'carrier' in printed

# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""`sets:` and `properties:`: what they load as, and every refusal decided at load."""

from __future__ import annotations

from typing import Any

import pytest

from mathspec import merge, override, to_spec
from mathspec._typesetting import FORMATS, typeset
from mathspec.errors import LanguageError
from mathspec.program import Relation
from tests.fixtures import varied

MODEL: dict[str, Any] = {
    'dimensions': {
        'generator': {},
        'bus': {},
        'line': {},
        'entity': {},
        'port': {},
        'period': {'dtype': 'int'},
        'snapshot': {'dtype': 'int', 'ordered': True},
        'zone': {},
    },
    'sets': {
        'connection': {'dims': ['entity', 'port'], 'missing': 'absent'},
        'generator_period': {'dims': ['generator', 'period']},
        'cover': {
            'dims': {'generator': 'generator', 'start': 'snapshot', 'covered': 'snapshot'},
            'missing': 'absent',
        },
    },
    'properties': {
        'generator': {'bus': 'bus'},
        'line': {'bus0': 'bus', 'bus1': {'into': 'bus', 'missing': 'absent'}},
        'snapshot': {'period': 'period', 'rep': 'snapshot'},
        'connection': {'bus': 'bus'},
        'generator_period': {'zone': 'zone'},
    },
    'parameters': {'eff': {'dims': ['entity', 'port'], 'where': 'connection'}},
    'variables': {'inj': {'dims': ['entity', 'port', 'snapshot'], 'where': 'connection'}},
}


def _refusal(**patch: Any) -> str:
    """The message `to_spec` refuses *MODEL* patched with, and it has to refuse."""
    with pytest.raises(LanguageError) as caught:
        to_spec(varied(MODEL, **patch))
    return str(caught.value)


@pytest.mark.parametrize(
    ('name', 'lowered'),
    [
        pytest.param(
            'connection',
            Relation((('entity', 'entity'), ('port', 'port')), ('entity', 'port'), 'absent'),
            id='a-set-is-a-bare-relation-under-its-name',
        ),
        pytest.param(
            'cover',
            Relation(
                (('generator', 'generator'), ('start', 'snapshot'), ('covered', 'snapshot')),
                ('generator', 'start', 'covered'),
                'absent',
            ),
            id='a-set-with-named-members',
        ),
        pytest.param(
            'generator.bus',
            Relation((('generator', 'generator'), ('bus', 'bus')), ('generator',), 'refused', subject='generator'),
            id='a-property-of-a-dimension',
        ),
        pytest.param(
            'line.bus1',
            Relation((('line', 'line'), ('bus1', 'bus')), ('line',), 'absent', subject='line'),
            id='a-property-a-row-may-lack',
        ),
        pytest.param(
            'snapshot.rep',
            Relation((('snapshot', 'snapshot'), ('rep', 'snapshot')), ('snapshot',), 'refused', subject='snapshot'),
            id='a-property-into-its-own-dimension',
        ),
        pytest.param(
            'connection.bus',
            Relation(
                (('entity', 'entity'), ('port', 'port'), ('bus', 'bus')),
                ('entity', 'port'),
                'refused',
                subject='connection',
            ),
            id='a-property-of-a-set-is-keyed-by-its-members',
        ),
    ],
)
def test_a_set_and_a_property_lower_to_a_relation(name, lowered):
    assert to_spec(MODEL).program.relations[name] == lowered


def test_every_set_and_property_is_a_relation_of_the_program():
    assert sorted(to_spec(MODEL).program.relations) == [
        'connection',
        'connection.bus',
        'cover',
        'generator.bus',
        'generator_period',
        'generator_period.zone',
        'line.bus0',
        'line.bus1',
        'snapshot.period',
        'snapshot.rep',
    ], 'one relation per set and one per property, and nothing else'


def test_a_mask_reads_a_set():
    program = to_spec(MODEL).program
    assert program.variables['inj'].where is not None
    assert program.variables['inj'].where.names_read == {'connection'}
    assert program.parameters['eff'].where is not None
    assert program.parameters['eff'].where.names_read == {'connection'}


def test_the_file_writes_back_each_property_as_it_was_written():
    written = to_spec(MODEL).to_dict()
    assert written['properties'] == MODEL['properties'], 'the short form where into is all a property says'
    assert written['sets']['generator_period'] == {'dims': ['generator', 'period']}, 'missing: refused is left out'
    assert to_spec(written) == to_spec(MODEL)


def test_the_normal_form_sorts_the_properties_of_a_subject():
    spec = to_spec(varied(MODEL, **{'properties.line': {'bus1': 'bus', 'bus0': 'bus'}}))
    assert spec.to_yaml(canonical=True) == to_spec(
        varied(MODEL, **{'properties.line': {'bus0': 'bus', 'bus1': 'bus'}})
    ).to_yaml(canonical=True)


def test_an_error_lists_no_property_as_a_name_to_write():
    message = _refusal(**{'variables.inj.where': 'wired'})
    assert "Relations: ['connection', 'cover', 'generator_period']" in message, (
        'a property has no name a file can write, so the listing leaves it out'
    )


@pytest.mark.parametrize('fmt', FORMATS)
def test_the_typesetter_prints_a_file_with_sets_and_properties(fmt):
    assert 'generator' in typeset(MODEL, fmt)


@pytest.mark.parametrize(
    ('patch', 'fragment'),
    [
        pytest.param(
            {'variables.inj.dims': ['connection', 'snapshot']},
            "Variable 'inj' is over set 'connection', and no entry is over a set. Write dims: "
            '[entity, port, snapshot] with where: connection.',
            id='a-variable-over-a-set',
        ),
        pytest.param(
            {'parameters.cost': {'dims': ['cover']}},
            "Parameter 'cost' is over set 'cover', and no entry is over a set. Write dims: [generator, snapshot] "
            'with where: cover.',
            id='a-parameter-over-a-set-with-two-members-over-one-dimension',
        ),
        pytest.param(
            {'given.expressions.flow': {'dims': ['connection']}},
            "Given expression 'flow' is over set 'connection'",
            id='a-given-entry-over-a-set',
        ),
        pytest.param(
            {'sets.tag': {'dims': ['generator']}},
            "Set 'tag' has 1 member(s), and needs at least two under 'dims:'. For a subset of one dimension, "
            'declare a bool parameter instead.',
            id='a-set-with-one-member',
        ),
        pytest.param(
            {'sets.pair': {'dims': ['bus', 'bus']}},
            "Set 'pair' names dimension 'bus' twice under 'dims:'. Name the two members: dims: {bus0: bus, bus1: bus}.",
            id='a-set-over-one-dimension-twice-without-names',
        ),
        pytest.param(
            {'sets.nested': {'dims': ['connection', 'snapshot']}},
            "Set 'nested' names set 'connection', and a set is not a dimension. Name its dimensions: entity, port.",
            id='a-set-of-a-set',
        ),
        pytest.param(
            {'sets.odd': {'dims': ['generator', 'nowhere']}},
            "Set 'odd' references undeclared dimension 'nowhere'.",
            id='a-set-over-an-undeclared-dimension',
        ),
        pytest.param(
            {'sets.odd': {'dims': {'bus': 'generator', 'zone2': 'zone'}}},
            "Set 'odd' names member 'bus' after dimension 'bus', but the member is over 'generator'.",
            id='a-member-named-after-another-dimension',
        ),
        pytest.param(
            {'properties.nowhere': {'bus': 'bus'}},
            "Properties of 'nowhere': 'nowhere' is neither a dimension nor a set.",
            id='a-subject-that-is-neither-a-dimension-nor-a-set',
        ),
        pytest.param(
            {'properties.parameter_subject': {'bus': 'bus'}, 'parameters.parameter_subject': {'dims': []}},
            "Properties of 'parameter_subject': 'parameter_subject' is neither a dimension nor a set.",
            id='a-parameter-as-a-subject',
        ),
        pytest.param(
            {'properties.generator.at': 'connection'},
            "Property 'generator.at' maps into set 'connection', and a property maps into one dimension. Declare "
            'one property for each of entity, port.',
            id='a-property-into-a-set',
        ),
        pytest.param(
            {'properties.generator.where_to': 'nowhere'},
            "Property 'generator.where_to' references undeclared dimension 'nowhere'.",
            id='a-property-into-an-undeclared-dimension',
        ),
        pytest.param(
            {'properties.connection.port': 'bus'},
            "Property 'connection.port' has the name of a member of the key of 'connection'",
            id='a-property-named-as-a-member-of-its-set',
        ),
        pytest.param(
            {'properties.snapshot.snapshot': 'snapshot'},
            "Property 'snapshot.snapshot' has the name of a member of the key of 'snapshot'",
            id='a-property-named-as-its-dimension',
        ),
        pytest.param(
            {'properties.generator.zone': 'bus'},
            "Property 'generator.zone' is named after dimension 'zone', but maps into 'bus'. Rename the property "
            'after what it holds.',
            id='a-property-named-after-another-dimension',
        ),
        pytest.param(
            {'properties.cover': {'crew': 'zone'}},
            "Properties of 'cover': the set has two members over 'snapshot' (['start', 'covered'])",
            id='a-property-of-a-set-with-two-members-over-one-dimension',
        ),
        pytest.param(
            {'parameters.connection': {'dims': ['entity']}},
            "Parameter 'connection' collides with the set of the same name. Rename one of them.",
            id='a-set-shares-the-namespace',
        ),
        pytest.param(
            {'properties.generator': {'2bus': 'bus'}},
            "properties: generator: '2bus' is not a name.",
            id='a-property-name-a-call-cannot-write',
        ),
        pytest.param(
            {'sets.connection.key': ['entity', 'port']},
            "unknown key 'key' in a set entry. Valid keys: description, dims, missing.",
            id='a-set-written-as-a-relation',
        ),
        pytest.param(
            {'properties.generator.bus': {'into': 'bus', 'values': 'bus'}},
            "unknown key 'values' in a property entry. Valid keys: description, into, missing.",
            id='a-property-with-an-unknown-key',
        ),
    ],
)
def test_a_set_or_a_property_the_language_refuses(patch, fragment):
    assert fragment in _refusal(**patch)


@pytest.mark.parametrize(
    ('path', 'written', 'fragment'),
    [
        pytest.param(
            'sets.connection.missing', 0, 'missing: 0 on a set, which takes refused or absent', id='set-a-number'
        ),
        pytest.param('sets.connection.missing', None, 'missing: null on a set says nothing', id='set-null'),
        pytest.param(
            'properties.line.bus1', {'into': 'bus', 'missing': 'bus2'}, 'missing: bus2 on a property', id='a-label'
        ),
        pytest.param(
            'properties.line.bus1',
            {'into': 'bus', 'missing': True},
            'missing: true on a property, which takes refused or absent',
            id='property-a-flag',
        ),
        pytest.param(
            'properties.line.bus1',
            {'into': 'bus', 'missing': None},
            'missing: null on a property says nothing',
            id='property-null',
        ),
    ],
)
def test_a_missing_that_reads_a_value_is_refused(path, written, fragment):
    """`missing:` on a set or a property asks about a key, so it takes only the two words."""
    assert fragment in _refusal(**{path: written})


@pytest.mark.parametrize(
    ('patch', 'properties'),
    [
        pytest.param('properties: {generator: {zone: zone}}\n', {'bus': 'bus', 'zone': 'zone'}, id='add'),
        pytest.param(
            'properties: {generator: {bus: {missing: absent}}}\n',
            {'bus': {'into': 'bus', 'missing': 'absent'}},
            id='edit-a-short-form',
        ),
        pytest.param('properties: {generator: {bus: null}}\n', None, id='remove-the-last'),
        pytest.param('properties: {generator: null}\n', None, id='remove-the-subject'),
    ],
)
def test_a_patch_lays_over_one_subject_at_a_time(patch, properties):
    laid = override(to_spec(MODEL), [patch]).to_dict()['properties']
    assert laid.get('generator') == properties
    assert laid['line'] == MODEL['properties']['line'], 'a patch to one subject keeps the others'


def test_a_patch_that_creates_a_property_writes_it_whole():
    with pytest.raises(LanguageError, match=r"edits the property 'zone'.*a property needs `into`"):
        override(to_spec(MODEL), ['properties: {generator: {zone: {missing: absent}}}\n'])


def test_two_fragments_that_declare_one_subject_are_refused():
    fragment = {'dimensions': {'generator': {}, 'bus': {}}, 'properties': {'generator': {'bus': 'bus'}}}
    with pytest.raises(LanguageError, match="both declare the properties of 'generator'"):
        merge([fragment, fragment])

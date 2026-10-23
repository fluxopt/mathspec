<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Sets and properties

You declare which combinations of labels exist as a **set**, and a fact about
each row of a dimension or a set as a **property**. The data supplies the rows
of both.

```yaml
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  line: { dtype: str }
  period: { dtype: int }
  zone: { dtype: str }
sets:
  connection: { dims: [generator, bus], missing: absent } # the pairs that are wired
  generator_period: { dims: [generator, period] }
properties:
  generator:
    bus: bus # each generator is on one bus
  line:
    bus0: bus
    bus1: { into: bus, missing: absent } # a line may have an open end
  generator_period:
    zone: zone # each generator is in one zone in each period
```

## `sets`

A set is a table whose rows are combinations of labels. `connection` holds the
pairs of a generator and a bus that are wired, and every other pair is not in
the set.

| Field         |                                                                          |                   |
| ------------- | ------------------------------------------------------------------------ | ----------------- |
| `dims`        | required. The dimensions a row combines, as a list or as a mapping       |                   |
| `missing`     | `refused` or `absent`: whether every combination of `dims` is a row      | default `refused` |
| `description` | free text                                                                | default `null`    |

A set has at least two dimensions. For a subset of one dimension, declare a
`bool` parameter. Where two members of a set are over one dimension, the
mapping form names them, and each name is a column of the set's table:

```yaml
dimensions:
  generator: { dtype: str }
  snapshot: { dtype: int, ordered: true }
sets:
  cover: { dims: { generator: generator, start: snapshot, covered: snapshot }, missing: absent }
```

A member is named after its own dimension or after no dimension, so
`dims: {bus: generator, zone: zone}` is refused. A set names dimensions only,
and a set in the `dims:` of another set is refused.

### Entries over a set

No parameter, variable, constraint or expression is over a set. An entry is
over the dimensions of the set, and its `where:` names the set:

```yaml
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  snapshot: { dtype: int }
sets:
  connection: { dims: [generator, bus], missing: absent }
parameters:
  load: { dims: [bus, snapshot] }
variables:
  flow:
    dims: [generator, bus, snapshot]
    where: connection
    bounds: { lower: 0 }
constraints:
  balance:
    dims: [bus, snapshot]
    expression: sum(flow, over=generator) == load
```

$$\mathit{flow}_{g,b,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B},\ t \in \mathcal{T} \,:\, \left( g,\ b \right) \in \mathrm{connection}$$

`flow` is [absent](absence.md) at every pair that `connection` does not list.
A parameter's `where:` reads a set in the same way
([a parameter's mask](parameters-variables-constraints.md#a-parameters-mask)).
An entry written over the set is refused, and the message names the rewrite:

```text
Variable 'flow' is over set 'connection', and no entry is over a set. Write dims: [generator, bus, snapshot] with where: connection.
```

## `properties`

A property maps each row of its **subject** to one label of a dimension. The
subject is a dimension or a set, and `properties:` lists the properties of each
subject under the subject's name. `generator: {bus: bus}` gives each generator
one bus.

| Field         |                                                                      |                   |
| ------------- | -------------------------------------------------------------------- | ----------------- |
| `into`        | required. The dimension the value is a label of                      |                   |
| `missing`     | `refused` or `absent`: whether every row of the subject has it       | default `refused` |
| `description` | free text                                                            | default `null`    |

`bus: bus` is the short form of `bus: {into: bus}`. Two properties of one
subject may map into one dimension, as `bus0` and `bus1` do. A property of a
set maps each row of the set, so `generator_period: {zone: zone}` gives each
generator one zone in each period.

`to_spec` refuses a property in these cases:

- The subject is not a declared dimension or set.
- `into:` is not a declared dimension. A property maps into one dimension, so
  for a set, declare one property for each dimension of the set.
- The property has the name of a member of its subject. `connection: {bus: zone}`
  is refused, because `bus` is a member of `connection`.
- The property is named after a dimension it does not map into. `period: zone`
  is refused. Name the property after what it holds.
- The subject is a set with two members over one dimension, such as `cover`.
  A subject has one member over each dimension.

A property name is not declared in the namespace of the file, so two subjects
can both have a property `bus`.

## A missing row

`missing:` checks a key at two levels, and never a value. A value that is not a
label of its dimension is refused when the data is attached, so no value fills
a gap.

| On a       | `missing:` asks                                      | `absent` means                                     |
| ---------- | ---------------------------------------------------- | -------------------------------------------------- |
| set        | is every combination of `dims` a row?                | a combination with no row is not in the set        |
| property   | does every row of the subject have the property?     | a row of the subject with no value lacks it        |

The default `refused` refuses data that leaves a row out. For
`generator_period` above, every pair of a generator and a period is a row, and
every one of those rows has a `zone`. For `connection`, only the listed pairs
are rows, and a property of `connection` with `missing: refused` needs a value
at each listed pair, not at every pair of a generator and a bus.

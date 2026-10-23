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

| Field         |                                                                     |                   |
| ------------- | ------------------------------------------------------------------- | ----------------- |
| `dims`        | required. The dimensions a row combines, as a list or as a mapping  |                   |
| `missing`     | `refused` or `absent`: whether every combination of `dims` is a row | default `refused` |
| `description` | free text                                                           | default `null`    |

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

| Field         |                                                                |                   |
| ------------- | -------------------------------------------------------------- | ----------------- |
| `into`        | required. The dimension the value is a label of                |                   |
| `missing`     | `refused` or `absent`: whether every row of the subject has it | default `refused` |
| `description` | free text                                                      | default `null`    |

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

| On a     | `missing:` asks                                  | `absent` means                              |
| -------- | ------------------------------------------------ | ------------------------------------------- |
| set      | is every combination of `dims` a row?            | a combination with no row is not in the set |
| property | does every row of the subject have the property? | a row of the subject with no value lacks it |

The default `refused` refuses data that leaves a row out. For
`generator_period` above, every pair of a generator and a period is a row, and
every one of those rows has a `zone`. For `connection`, only the listed pairs
are rows, and a property of `connection` with `missing: refused` needs a value
at each listed pair, not at every pair of a generator and a bus.

The typeset legend prints each set and each property beside the dimensions it
reads: `connection ⊆ G × B`, `bus: G → B`, and `zone: generator_period → Z` for
a property of a set. Beside them it prints
`` `line[bus1]` is `absent` where the data has no row `` for each one that
declares `missing: absent`, and prints nothing for `refused`.

## How a set or a property is read

A call reads one subject and names what it reads as `subject[name, …]`. Each
name is a member of the subject or a property of it. The call **joins** the
operand to the subject's table on the columns they share, and **groups** what
the join produces. A member is a key column of that table, and a property is a
value column.

| kind              | what it does                                                              | written as                                                         |
| ----------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| join and group by | rows of the operand match rows of the table, and each group is added up   | `sum(p, over=generator, by=generator[bus])`                        |
| join              | each row of the operand matches one row of the table, and reads its value | `at(price, by=generator_period[zone])`                             |
| partition         | the dimensions stay, and the rows are grouped                             | `shift(x, along=snapshot, offset=1, within=snapshot[period])`      |
| test              | a row's value or its presence keeps or cuts a coordinate                  | `generator[bus] == 'b1'`, `line[bus0] != line[bus1]`, `line[bus1]` |

Four rules hold for every call:

1. A call names every column it reads, so `at(price, by=generator)` is
   refused. Write `at(price, by=generator[bus])`.
2. A property the call does not name is not read.
3. A call reads one subject. To read through two, nest the calls:
   `sum(sum(p, over=generator, by=generator[bus]), over=bus, by=bus[zone])`.
4. A dimension the subject does not name passes through to the result.

### Sums

`sum(x, over=d, by=s[c])` sums `x` over the columns in `over=`, grouped by the
columns in `by=`. As in `sum(x, over=d)`, `over=` names what the result loses,
and `by=` names what the result gains. Either may be a list.

Each column of the subject's table is either **joined on** or not, and either
**grouped by** or not. The call decides both:

| column of the table               | joined on | grouped by | in the result |
| --------------------------------- | --------- | ---------- | ------------- |
| a column in `over=`               | yes       | no         | removed       |
| a column in `by=`                 | no        | yes        | added         |
| a member the call does not name   | yes       | yes        | kept          |
| a property the call does not name | no        | no         | not read      |

With the set `generator_period: { dims: [generator, period] }` and its
property `zone`, the set `connection: { dims: [generator, bus] }`, and `p`
over `[generator, period]`:

| call                                                | joins on            | groups by         | result              |
| --------------------------------------------------- | ------------------- | ----------------- | ------------------- |
| `sum(p, over=generator, by=generator_period[zone])` | `generator, period` | `zone, period`    | `[period, zone]`    |
| `sum(p, over=period, by=generator_period[zone])`    | `period, generator` | `zone, generator` | `[generator, zone]` |
| `sum(p, over=generator, by=connection[bus])`        | `generator`         | `bus`             | `[bus, period]`     |

- The result is the operand, less the dimensions in `over=`, plus the columns
  in `by=`. The operand carries every column joined on, and none that the call
  groups by. With `load` over `bus`, `sum(load * p, over=generator, by=generator[bus])`
  is refused. Write `load * sum(p, over=generator, by=generator[bus])`.
- A name in `over=` is a column of the subject's table, or else a dimension.
  With `snapshot: {rep: snapshot}`, `sum(x, over=snapshot, by=snapshot[rep])`
  joins on the member `snapshot` and groups by `rep`. A name in both `over=` and
  `by=` is refused.
- A dimension in `over=` that no column is named after is summed away after the
  group-by. `sum(p, over=[generator, period], by=generator[bus])` adds up each
  bus over every period.
- A sum adds up several rows per group. Where the columns grouped by are every
  member of the subject, every group is one row. That is a join with no
  group-by, which is `at`, so `to_spec` refuses the sum and names `at`:

  ```text
  Named expression 'e': sum(by=generator_period[generator, period]): the columns this sum groups by, ['generator', 'period'], hold the whole key ['generator', 'period'], so every group is one row and the sum adds nothing. Write at(..., by=generator_period[zone]), or group by a property.
  ```

### Lookups

`at(x, by=s[c])` reads `x` at the value of property `c`, once for every row of
the subject. It joins `x` on the properties in `by=` and groups by the members,
so every group is one row.

- A lookup reads properties. A member in `by=` is refused, and so is a set read
  by its members alone, where a row is its own key. Sum through it instead.
- The result gains the members, except where the operand carries them already.
  A member over a dimension the operand carries is joined on too, unless a
  property in `by=` already maps into that dimension. With `price` over
  `[zone, period]`, `at(price, by=generator_period[zone])` joins on `zone` and
  `period`, and its result is `[generator, period]`.
- No two properties in `by=` map into one dimension, because the operand
  carries each dimension once.

### Partitions

`shift(x, along=d, within=s[c])`, `sum_back(x, along=d, within=s[c])` and
`position(d, within=s[c])` step along the member over `d`, join on the other
members, and partition the rows by the properties in `within=`. The
dimensions do not change. A set read by its members alone partitions nothing,
and a coordinate with no value for the property is in no group.

### Tests

A condition reads a subject at the coordinates of its own entry:

- `generator[bus] == 'b1'` compares a property against a label, and
  `line[bus0] != line[bus1]` compares two properties into one dimension. A
  comparison reads one property, and it is false where the row lacks it,
  whatever the operator.
- `line[bus1]` alone is true where the line has the property, and
  `generator[bus, carrier]` is true where the row has both.
- A set's bare name is true where the set has a row
  ([entries over a set](#entries-over-a-set)).

### Several properties

```yaml
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  carrier: { dtype: str }
  snapshot: { dtype: int }
properties:
  generator:
    bus: bus
    carrier: { into: carrier, missing: absent }
parameters:
  limit: { dims: [bus, carrier] }
variables:
  p:
    dims: [generator, snapshot]
    where: generator[carrier]
    bounds: { lower: 0 }
constraints:
  carrier_limit:
    dims: [bus, carrier, snapshot]
    expression: sum(p, over=generator, by=generator[bus, carrier]) <= limit
```

$$p_{g,t} \ge 0 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T} \,:\, \mathrm{carrier}(g) \text{ is defined}$$

$$\sum_{g \in \mathcal{G} \,:\, \mathrm{bus}(g) = b \wedge \mathrm{carrier}(g) = c} p_{g,t} \le \mathrm{limit}_{b,c} \qquad \forall\, b \in \mathcal{B},\ c \in \mathcal{C},\ t \in \mathcal{T}$$

A call that names several properties reads their **inner join**. A generator
with no `carrier` has no row in it, so `carrier_limit` adds up only the
generators that have a bus and a carrier. A dimension is read by its
properties, because it has no table of its own:

```text
Constraint 'carrier_limit': sum(by=generator[generator]) reads no property of 'generator', and a dimension has no table of its own. Name one of its properties, ['bus', 'carrier'].
```

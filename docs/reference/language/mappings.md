<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Mappings

A **mapping** gives each label of a [dimension](dimensions.md) one label of
another dimension, such as the bus of each generator. With mappings declared, a
sum can group by them, a lookup can read through them, and a condition can
test them. The file declares the mappings, and the labels come with the data. A
set of combinations of labels, such as the buses that each generator may
connect to, is a dimension with [members](dimensions.md#over).

## `mappings`

Each key under `mappings:` names a **subject**, which is a dimension. Each key
under the subject declares one mapping, which gives every label of the subject one
label of the dimension that `dim:` names.

```yaml
dimensions:
  bus: { dtype: str }
  generator: { dtype: str }
  line: { dtype: str }
mappings:
  generator:
    bus: { dim: bus } # each generator is on one bus
  line:
    bus0: { dim: bus }
    bus1: { dim: bus, missing: absent } # a line may have an open end
```

A mapping always writes `dim:`, and has no shorter form. A condition or an operator
reads a mapping as `subject[mapping]`, so `generator[bus]` is the bus of a generator.

A dimension that lists its members under [`over:`](dimensions.md#over) already
has a mapping per member, named after the member and under `missing: refused`. So
`connection[unit]` is the unit of a connection, and every call on this page
reads a member as it reads a mapping under `mappings:`.

| Key           | What it sets                                                                        | Default   |
| ------------- | ----------------------------------------------------------------------------------- | --------- |
| `dim`         | required. The dimension whose labels the mapping gives                              |           |
| `missing`     | [`refused` or `absent`](#missing): whether every label of the subject needs a label | `refused` |
| `description` | free text                                                                           | `null`    |

A mapping is named after the dimension it refers to, or after no dimension. The
typesetter prints a mapping as a function from its subject into that dimension, so
`generator[bus]` prints as $`\mathrm{bus}: \mathcal{G} \to \mathcal{B}`$.
mathspec refuses a mapping at load in five cases:

- The subject is not a dimension.
- `dim:` names no dimension.
- The mapping is named after a dimension that it does not refer to.
- The mapping has the name of its subject.
- The mapping has the name of a member of its subject.

With `generator: { period: { dim: zone } }`, mathspec prints:

```text
mappings: 'generator': mapping 'period' is named after dimension 'period', but refers to 'zone'. Rename the mapping after what it holds.
```

### Cardinalities

How many labels a label may have (the cardinality) decides whether a fact is a
mapping or a dimension with members:

| What the file states                         | Written                                                                                                       | Cardinality                     |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| each generator has one bus                   | `mappings: { generator: { bus: { dim: bus } } }`                                                              | many-to-one                     |
| a generator may connect to several buses     | `dimensions: { connection: { over: [generator, bus] } }`                                                      | many-to-many                    |
| a generator has one zone in each period      | `dimensions: { zone_of: { over: [generator, period] } }` and `mappings: { zone_of: { zone: { dim: zone } } }` | many-to-one, from a pair        |
| a snapshot has a month, a week and a weekday | `mappings: { snapshot: { month: { dim: month }, week: { dim: week }, weekday: { dim: weekday } } }`           | three mappings of one subject   |
| a line has two ends, both buses              | `mappings: { line: { bus0: { dim: bus }, bus1: { dim: bus } } }`                                              | two mappings into one dimension |
| a snapshot has a representative snapshot     | `mappings: { snapshot: { rep: { dim: snapshot } } }`                                                          | many-to-one, onto itself        |
| a snapshot has neighbours                    | `dimensions: { next_snapshot: { alias: snapshot }, neighbour: { over: [snapshot, next_snapshot] } }`          | many-to-many, onto itself       |

## `missing`

`missing:` on a mapping sets whether every label of the subject needs a label of
the mapping. On a dimension with members, it sets whether every combination of the
members needs a tuple ([`missing` of a dimension](dimensions.md#missing)).

```yaml
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  line: { dtype: str }
mappings:
  generator:
    bus: { dim: bus } # refused: every generator is on a bus
  line:
    bus0: { dim: bus }
    bus1: { dim: bus, missing: absent } # an open end is meant
```

<figure class="diagram">
--8<-- "docs/static/relations-missing.svg"
</figure>

At `l3`, the data gives `line[bus1]` no label, so `line[bus1]` is absent there.

| `missing:`            | Result                                                                              |
| --------------------- | ----------------------------------------------------------------------------------- |
| `refused`, by default | a tool refuses the data when it is attached, and names the label                    |
| `absent`              | a label with no label of the mapping maps to nothing, which is [absent](absence.md) |

No number can replace a missing label, so at load mathspec refuses a value
such as `missing: 0`:

```text
mappings.generator.bus.missing: missing: 0 on a mapping, which takes refused or absent. A row with nothing there is refused, or is not in the data.
```

The typeset legend lists `` `line[bus1]` is `absent` where the data gives no label ``
beside the dimension of the subject, and nothing for `refused`.

## The data contract

With data attached, each subject with mappings has one table, named after it. The
table has one column for the subject and one column per mapping, named after the
mapping. So the data for the mappings of `line` is a table `line` with the columns
`line`, `bus0` and `bus1`. A piece of software that reads a spec
([a tool](../glossary.md#tool)) requires five things of a table:

- The table has one row per label of the subject, so a generator with two
  rows, on two buses, is refused.
- Every label in the column of a mapping is a label of the dimension it refers to,
  and a label that matches none is refused.
- The table has a row for every label of the subject.
- A null is refused, except in the column of a mapping that declares
  `missing: absent`.
- The order of the rows has no meaning, because the order comes from the
  [dimension](dimensions.md#ordered).

A mapping has no `where:`, so its labels come from the data alone. A tool
therefore knows them before it evaluates any condition, such as the
[`where:` of a parameter](parameters-variables-constraints.md#where).

An [assumption](assumptions.md) can require labels of a mapping. For `line[bus1]`
[above](#missing), `{holds: "line[bus1]", where: "closed"}` requires an end for
every closed line, where `closed` is a `bool` parameter over `line`.

## How mappings are used

A call **joins** the expression it acts on (its operand) to the table of a
subject on their shared columns, and then **groups** the rows it has joined.
In a call, `s[c]` names the subject `s` and its column `c`, and `s[c, …]`
names several columns of one table. A column is a mapping of `s`, or a member of
`s`. The subject appears once, so one call uses one table.

| Kind              | What it does                                                              | Written as                                         |
| ----------------- | ------------------------------------------------------------------------- | -------------------------------------------------- |
| join and group by | rows of the operand match rows of the table, and each group is added up   | `sum(x, over=d, by=s[c])`                          |
| join              | each row of the operand matches one row of the table, and takes its label | `at(x, by=s[m])`                                   |
| partition         | the dimensions stay, and the rows are grouped                             | `shift`, `sum_back`, `position` with `within=s[m]` |
| test              | a coordinate stays where the mapping has a label                          | `s[m]` in a condition                              |

Four rules apply to every call:

1. A call lists every column it uses.
2. A mapping that the call does not list is not used.
3. The key of a subject, the subject itself, cannot change in a call.
4. A dimension that no column of the table is over passes through to the
   result.

Under the first rule, mathspec refuses `at(x, by=generator)`, and the message
lists the mappings of the subject:

```text
Constraint 'c': at(by=generator) names the subject and none of its mappings. Write by=generator[<mapping>], with a mapping of 'generator': ['bus'].
```

### Sums

`sum(x, over=d, by=s[c])` sums `x` over the dimensions in `over=`, grouped by
the columns in `by=`. As in `sum(x, over=d)`, `over=` lists what the result
loses and `by=` lists what it gains, and either one may be a list. A sum
through a table adds each row of `x` only to the group that the table gives
it.

<figure class="diagram">
--8<-- "docs/static/relations-sum-by.svg"
</figure>

`north` adds up `wind` and `gas`, and `south` is `solar` alone.

Over a dimension with members, a sum groups by members and mappings alike. With
`zone_of` over `[generator, period]` and its mapping `zone`, `connection` over
`[generator, bus]`, and a variable `p` over `[generator, period]`, three sums
have three results:

| Call                                                                                   | Result              |
| -------------------------------------------------------------------------------------- | ------------------- |
| `sum(at(p, by=zone_of[generator, period]), over=zone_of, by=zone_of[period, zone])`    | `[period, zone]`    |
| `sum(at(p, by=zone_of[generator, period]), over=zone_of, by=zone_of[generator, zone])` | `[generator, zone]` |
| `sum(at(p, by=connection[generator]), over=connection, by=connection[bus])`            | `[bus, period]`     |

`at()` reads `p` at each tuple first, and the sum then adds the tuples of each
group. Four more rules apply to a sum through a table:

- The operand is over the subject, and over no column that the call groups by.
- A name in `over=` is the subject, or else a dimension. With the mapping `rep` of
  `snapshot`, `sum(x, over=snapshot, by=snapshot[rep])` sums over `snapshot`
  and groups by `rep`.
- A name in both `over=` and `by=` is refused.
- A dimension in `over=` that no column is named after is summed away after
  the call groups the rows. So
  `sum(p, over=[generator, period], by=generator[bus])` adds up each bus over
  every period.

Under the first rule, with `load` over `[bus]`, mathspec refuses
`sum(load * p, over=generator, by=generator[bus])` and prints:

```text
Constraint 'c': sum(by=generator[bus]) groups by ['bus'], which the expression already carries.
Move the factor carrying ['bus'] outside the operator, or group by a mapping into another dimension.
```

`load * sum(p, over=generator, by=generator[bus])` is accepted, because the
sum no longer has `load` inside it. A sum over a member of a dimension with
members is refused, with the rewrite through the dimension:

```text
Constraint 'c': sum(by=zone_of[zone]): over=generator names a member of 'zone_of', which is one dimension here. Write sum(at(p, by=zone_of[generator]), over=zone_of, by=zone_of[zone]).
```

### Lookups

`at(x, by=s[m])` takes the value of `x` at the label that mapping `m` gives each
label of `s`. It joins `x` on the mappings in `by=` and groups by the subject, so
every group is one row. A lookup adds up nothing, and each row of the result
is the value of `x` at one coordinate. With a variable `build` over `[bus]`,
`at(build, by=line[bus0])` has one row per line:

<figure class="diagram">
--8<-- "docs/static/relations-at.svg"
</figure>

Lines `l1` and `l2` both take the value of `build` at `north`, and `l3` takes
it at `south`.

Three rules apply to a lookup:

- A lookup reads only mappings and members. The subject in `by=` is refused.
- The result gains the subject, unless the operand is already over it.
  `at(x, by=snapshot[rep])` joins on `rep` alone, so the result gains
  `snapshot`. With `p` over `[generator, period]`,
  `at(p, by=zone_of[generator, period])` is over `[zone_of]`.
- No two mappings in `by=` refer to one dimension, because the operand has one
  coordinate along each of its dimensions.

With `at(build, by=line[line])`, mathspec prints:

```text
Constraint 'c': at(by=line[line]) names ['line'], a column of 'line' itself. A lookup reads mappings at the row. Name one of its mappings, ['bus0', 'bus1'].
```

### Partitions

`shift(x, along=d, within=s[m])`, `sum_back(x, along=d, within=s[m])` and
`position(d, within=s[m])` step along `d`, the subject, and split its labels
into groups by the mappings in `within=`. The dimensions of the result do not
change. The result is absent at a coordinate that the mapping gives
[no group](operators.md#within). With the mapping `season` of `snapshot`,
`shift(soc, along=snapshot, offset=1, edge='wrap', within=snapshot[season])`
steps back within each season:

<figure class="diagram">
--8<-- "docs/static/relations-partition.svg"
</figure>

The first snapshot of each season takes the value of the last snapshot of the
same season, and no value crosses from winter to summer.

`within=` may list two mappings into one dimension, but not the subject. A
dimension with members has no order, so mathspec refuses it in `along=` and in
`within=`, and names an entry over the members as the rewrite.

### Tests

A condition tests a mapping at the coordinates of its own entry. It compares a
mapping, written `s[m]`, against a label, compares two mappings, or tests that a label
exists. [Conditions](expressions.md#conditions) lists when two mappings may be
compared. A comparison reads one mapping, so `snapshot[month, weekday] == 'x'` is
refused, and mathspec suggests the rewrite on the second line of the message:

```text
Variable 'x': Cannot parse the condition "snapshot[month, weekday] == 'x'".
a comparison reads one mapping of 'snapshot'. Compare each mapping on its own: snapshot[month] == … AND snapshot[weekday] == ….
Expected end of text, found '['  (at char 8), (line:1, col:9)
```

A mapping alone in a condition, such as `line[bus1]`, is true where the mapping gives
the label a label, and prints as $`\mathrm{bus1}(l) \text{ is defined}`$. The
bare name of a dimension with members tests its tuples
([the bare name in a condition](dimensions.md#the-bare-name-in-a-condition)):

```yaml title="flow.yaml"
dimensions:
  generator: { dtype: str }
  bus: { dtype: str }
  snapshot: { dtype: int }
  connection: { over: [generator, bus] } # the pairs that are wired
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

<figure class="diagram">
--8<-- "docs/static/relations-where-bare.svg"
</figure>

`flow` exists at the pairs that `connection` lists and is [absent](absence.md)
at every other pair, so `balance` adds up the generators wired to each bus.

!!! info "See also"

    - [mappings as linear maps](../../about/relations-as-linear-maps.md) for the
      same calls written as matrices

<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Maps as linear maps

A [`sum`](../reference/language/operators.md#sum) or an
[`at`](../reference/language/operators.md#at) through a table that gives each
label a label ([a map](../reference/language/maps.md#maps)) is the product
of a matrix and a vector. The maps page describes the same sum in
database words, "joined on" and "grouped by". The matrix form is the sum in
the form a paper uses.

Every formula below is over this spec:

```yaml
dimensions:
  snapshot: { dtype: int }
  generator: { dtype: str }
  zone: { dtype: str }
  zone_of: { over: [generator, snapshot] }
maps:
  zone_of: { zone: { dim: zone } }
parameters:
  zone_cap: { dims: [snapshot, zone] }
variables:
  p: { dims: [snapshot, generator] }
constraints:
  zonal:
    dims: [snapshot, zone]
    expression: sum(at(p, by=zone_of[generator, snapshot]), over=zone_of, by=zone_of[snapshot, zone]) <= zone_cap
  looked_up:
    dims: [zone_of]
    expression: at(p, by=zone_of[generator, snapshot]) <= at(zone_cap, by=zone_of[snapshot, zone])
objective:
  sense: minimize
  expression: sum(p)
```

`zonal` contains a sum of `p` through the map `zone_of[zone]`, and
`looked_up` a lookup of `zone_cap` through the same map. The spec loads.

## The indicator of a set of tuples

A dimension with [members](../reference/language/dimensions.md#over)
$`D_1, \dots, D_n`$ is a set of tuples, so it is a subset
$`K \subseteq D_1 \times \dots \times D_n`$. Its **indicator**
$`\mathbf{1}_K`$ is $`1`$ at a listed tuple and $`0`$ everywhere else. A
[map](../reference/language/maps.md#maps) gives each label of its subject one
label, so a map from the subject $`K`$ into the dimension $`V`$ is a function
$`f: K \to V`$. The set of pairs $`(k, f(k))`$ is a relation $`R`$ (the graph
of $`f`$), and its indicator is

```math
\mathbf{1}_R(k, v) = [\, f(k) = v \,].
```

The bracket is $`1`$ where $`f(k) = v`$ and $`0`$ elsewhere.

By default the function has a value at every tuple (it is total). With data
attached, the tool that builds the model
([an engine](../reference/glossary.md#tool)) checks for
[one row per label](../reference/language/maps.md#the-data-contract) of the
subject. Under [`missing: absent`](../reference/language/maps.md#missing), the
function has no value at a tuple with no label (it is partial). With
$`\mathcal{G}`$, $`\mathcal{T}`$ and $`\mathcal{Z}`$ the sets of generators,
snapshots and zones, `zone_of[zone]` in the spec above is a function
$`f: K \to \mathcal{Z}`$ on the tuples $`K \subseteq \mathcal{G} \times \mathcal{T}`$
that `zone_of` lists.

Each member is a map too: `zone_of[generator]` and `zone_of[snapshot]` send a
tuple to its labels. A dimension with members and no declared map has only
these maps, so one generator may sit in several tuples, each with its own
snapshot.

## A join and group-by as a contraction

`zonal` reads `p` at each tuple $`k = (g, t)`$ with `at`, multiplies by the
indicator of the graph of `zone_of[zone]`, and sums over the tuples:

```math
y_{t,z} = \sum_{k = (g,\,t) \in K} \mathbf{1}_R(k, z) \cdot p_{g,t} = \sum_{k \in K \,:\, \mathrm{snapshot}(k) = t \wedge f(k) = z} p_{\mathrm{generator}(k),\,\mathrm{snapshot}(k)}
```

<figure class="diagram">
--8<-- "docs/static/linear-maps-join.svg"
</figure>

With the data in the figure, the join pairs each row of `p` with the tuple of
`zone_of` that has the same generator and snapshot. The group-by adds the two
pairs in zone `north` at snapshot `0`, so the result `y` has three rows.

The typesetter [prints](../reference/notation.md) the right-hand form. The left-hand form is a sum over an index that two factors share (a
**tensor contraction**). The maps page describes each column of the table
by two properties. Each pair of properties is a position that an index can
take in the formula:

| On the maps page                      | In the formula                                                       |
| ------------------------------------- | -------------------------------------------------------------------- |
| joined on, the subject in `over=`     | $`k`$ is on both factors and summed. It is not in the result.        |
| grouped by, a map in `by=`            | $`z`$ is on the indicator alone and not summed. It is in the result. |
| grouped by, a member in `by=`         | $`t`$ is read off $`k`$ and not summed. It is in the result.         |
| neither, a map the call does not name | The map is not in the formula, and the sum does not use it.          |

The result has the **free indices**, which are the indices that are not
summed. They are the indices of the operand and of the indicator together,
less the summed one.

mathspec refuses a sum at load when the sum breaks one of two conditions, and the
formula needs each of them:

- The operand is over the subject. `p` is over `generator` and `snapshot`, so
  `at` reads it at each tuple first.
- The operand has no column grouped by. Otherwise $`z`$ would sit on both
  factors and not be summed. Then the product would match the two occurrences
  of $`z`$, and the result would gain no extra index (an axis) for $`z`$. You
  write that match outside the operator, as `zone_cap` times the sum.

At each $`t`$, the matrix $`M_t[z, g] = \mathbf{1}_R((g, t), z)`$ has one row
per zone and one column per generator, with entries of zero and one, and
$`y_t = M_t\, p_t`$. Over all snapshots, the member `snapshot` that the call
groups by makes the matrix zero outside one block per snapshot
(**block-diagonal**).

## A lookup through a map

`at(zone_cap, by=zone_of[snapshot, zone])` joins the same table, and sums
over the other index:

```math
w_{k} = \sum_{z} \mathbf{1}_R(k, z) \cdot \mathrm{zone\_cap}_{\mathrm{snapshot}(k),z} = \mathrm{zone\_cap}_{\mathrm{snapshot}(k),\, f(k)}
```

<figure class="diagram">
--8<-- "docs/static/linear-maps-at.svg"
</figure>

With the data in the figure, each tuple of `zone_of` takes the value of
`zone_cap` at its snapshot and zone. So at snapshot `0`, wind and gas both
take the value at `north`, and no row takes the value at `south`.

The indicator and the contraction are the same as for the sum, so the same
free-index rule sets the dimensions of the result. As a matrix, `at` is
$`M_t^{\mathsf{T}}`$. The tuples where $`f`$ has a value are its domain. Because $`R`$ is the
graph of $`f`$, the sum over $`z`$ has exactly one term at each tuple in
the domain.
It has no term elsewhere. So the contraction is the composition
$`\mathrm{zone\_cap} \circ f`$, which is a **pullback**: the value of
`zone_cap` at $`f(k)`$.

That one term is the difference between `at` and `sum`. An `at` is evaluated
at the subject, so each of its groups is always one tuple.

The two maps are **adjoint**. The sum of elementwise products (the inner
product) does not change when the matrix moves to the other side, flipped
over its diagonal (its transpose). With $`x`$ over generators and $`v`$ over
zones at one snapshot $`t`$,

```math
\langle M_t x, v \rangle = \sum_{z} v_z \sum_{g} \mathbf{1}_R(g, t, z)\, x_g = \sum_{g} x_g \sum_{z} \mathbf{1}_R(g, t, z)\, v_z = \langle x, M_t^{\mathsf{T}} v \rangle.
```

Both maps contract the same indicator. So the compiled spec
([the program](../reference/program.md)) has `at` as a `Join` node, and
`sum(by=)` as the same `Join` under a `Sum`.

## Why the language has no join operator

Two operators, `sum(by=)` and `at(by=)`, are better here than a `join` and a
`sum`. A separate `join` operator would return the product before the sum, with an
axis for the column grouped by, $`z`$. `sum(by=)` and `at(by=)` already add
that axis and remove it in one call, so a `join` would add nothing that a file
cannot state. mathspec refuses `join` as an unknown operator, and the message
lists the operators that exist.

## How an engine evaluates the product

The file states the formula, and an engine decides how to evaluate it. A
table lists the **support** of $`\mathbf{1}_R`$, which is the set of rows
where $`\mathbf{1}_R`$ is $`1`$. An engine can multiply a matrix stored that
way by a vector in two steps:

1. The engine pairs each row of the table with each row of the operand that
   agrees on every shared index, here $`g`$ and $`t`$ of each tuple. That is a join on the columns joined on that
   matches equal values (an inner equi-join). Each
   pair is one nonzero product $`1 \cdot p_{g,t}`$, and it takes the label of
   the column grouped by, $`z`$.
2. The engine adds the pairs that agree on the free indices, here $`(t, z)`$.
   That is a sum grouped by the dimensions of the result.

For `at`, an engine runs step 1 only, because with one row per group no two
pairs have the same coordinate. Where several tuples share one $`z`$, the
engine gets several rows for that $`z`$. Those rows are a column of
$`M_t^{\mathsf{T}}`$ with several ones.

So the database steps and the matrix product are one computation. The join step has only the entries where $`\mathbf{1}_R`$ is $`1`$, and the group-by is the
$`\sum`$.

## Empty groups and missing values

At two kinds of position the matrix product has no term.

- An empty group is an empty sum. With data attached, a zone that no
  generator maps to at $`t`$ has $`y_{t,z} = 0`$, and the row is
  $`0 \le \mathrm{zone\_cap}_{t,z}`$. The row has no variable. It exists once the data is attached. At load,
  mathspec refuses only a constraint whose expression has no variable, and the
  expression of `zonal` has `p`.
- Outside the domain of $`f`$ there is no value.
  $`\mathrm{zone\_cap} \circ f`$ is undefined where $`f`$ is undefined, so
  `at` has no row there (it is [absent](../reference/glossary.md#absence)), and
  [absence spreads](../reference/language/absence.md#how-absence-travels) to
  the row. Under the default, no tuple is outside the domain. `looked_up` is
  over `zone_of`, so a reader sees in the spec which rows exist.

<figure class="diagram">
--8<-- "docs/static/linear-maps-empty.svg"
</figure>

With the data in the figure, no generator maps to `south`, so both rows of
`zonal` at `south` are empty groups with no variable. `zone_of` lists no tuple
for `gas` at snapshot `1`, so the lookup has no row there either.

## Partitions and tests

The other two uses of a map, a
[partition](../reference/language/maps.md#partitions) and a
[test](../reference/language/maps.md#tests), are not matrix products. An
operator with `within=`, such as `shift`, works separately on each set of
members that $`f`$ sends to one value (a fibre). The dimensions of the result
do not change. With the map `snapshot: { season: { dim: season } }`,
`shift(soc, along=snapshot, offset=1, edge='wrap', within=snapshot[season])`
steps back within each season:

<figure class="diagram">
--8<-- "docs/static/relations-partition.svg"
</figure>

Each season is one fibre of `snapshot[season]`, so no value crosses from winter to
summer.

A test is an indicator. In a `where`, the bare name of a dimension with
members is $`\mathbf{1}_K`$ at the coordinate of the entry, and a map alone,
such as `zone_of[zone]`, is the indicator of the domain of $`f`$.

You can now judge the dimensions of a sum or an `at` through a map, and
why the language has no `join` operator.

!!! info "See also"

    - [maps](../reference/language/maps.md), for every key a map accepts
    - [how dimensions combine](../reference/language/expressions.md#how-dimensions-combine),
      for the rule that sets the free indices of every expression
    - [how absence travels](../reference/language/absence.md#how-absence-travels),
      for figures of the rows that absence removes
    - [sums through a map](../reference/language/maps.md#sums),
      for the messages mathspec prints when it refuses a sum
    - [constructs the language already has](limits.md#constructs-the-language-already-has),
      for the refused `join` operator and what you write instead
    - [the notation page](../reference/notation.md), for how the typesetter
      prints each use
    - [understanding a spec in SQL and dataframe terms](sql-and-dataframes.md),
      for the same operators as queries

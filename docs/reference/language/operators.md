<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Operators

An operator sums an expression over a dimension, or moves its values along one.
The set is **closed**: the four below, and
[`dual`](named.md#reading-a-constraints-dual) in a reported expression, are all
of them, and a file cannot add an operator. Write a composition of them as a [macro](named.md#macros).

| Operator                                                   | Result                                                                                                                                                            |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sum(array)`                                               | Every dimension that `array` carries collapses. The result is a scalar                                                                                            |
| `sum(array, over=dim)`                                     | `dim` collapses. `array` must carry `dim`                                                                                                                         |
| `sum(array, over=[a, …])`                                  | Each dimension in the list collapses. `array` must carry each one, and the list names each one once                                                               |
| `sum(array, over=dim, by=subject[p])`                      | `dim` collapses, and the result is grouped by the property `p`. The other members of the subject are joined on, so the array carries them and the result keeps them |
| `sum(array, over=[dim, …], by=subject[p, …])`              | The same with several dimensions and several properties of one subject. The call joins on them together, and groups by their product                              |
| `at(array, by=subject[p])`                                 | `array` read at the value of the property `p`, once per row of the subject. The result gains the subject's members                                                 |
| `shift(array, along=dim, offset=n)`                        | The value `n` positions earlier along `dim`. The vacated edge is **absent**                                                                                       |
| `shift(array, along=dim, offset=n, edge='wrap')`           | The value `n` positions earlier, counted cyclically, so nothing is vacated                                                                                        |
| `shift(array, along=dim, offset=n, edge=v)`                | The value `n` positions earlier, with the number `v` standing where the edge was vacated                                                                          |
| `shift(array, along=dim, offset=p, edge=…)`                | `p` is an integer parameter, so each entity is reached by its own offset                                                                                          |
| `shift(array, along=dim, offset=n, within=subject[p])`     | The translation steps inside each group that the property `p` makes. Neighbours, edges and a wrap all belong to that group                                        |
| `sum_back(array, along=dim, window=n)`                     | The sum of the last `n` positions along `dim`, ending at the position being written                                                                               |
| `sum_back(array, along=dim, window=p)`                     | `p` is an integer parameter, so each entity gets its own window length                                                                                            |
| `sum_back(array, along=dim, window=p, edge='wrap')`        | The window reaches around the axis, instead of stopping short at its start                                                                                        |
| `sum_back(array, along=dim, window=n, within=subject[p])`  | The window stays inside each group that the property `p` makes                                                                                                    |

`array` is any expression with the right dimension set, a parameter or a
variable. [Every operator as math](#every-operator-as-math) shows how each row
prints.

## `sum`

`sum(x)` on a scalar is an error. `sum(x, over=[a, b])` is
`sum(sum(x, over=a), over=b)`, and prints as one sum over both sets. A nodal
balance is one `sum(by=)` per kind of component:

```yaml
dimensions:
  bus: { dtype: str }
  generator: { dtype: str }
  line: { dtype: str }
properties:
  generator:
    bus: bus
  line:
    from_bus: bus
    to_bus: bus
parameters:
  load: { dims: [bus] }
variables:
  p: { dims: [generator] }
  f: { dims: [line] }
constraints:
  nodal_balance:
    dims: [bus]
    expression: >-
      sum(p, over=generator, by=generator[bus])
      + sum(f, over=line, by=line[to_bus])
      - sum(f, over=line, by=line[from_bus])
      == load
```

[How a set or a property is read](sets.md#how-a-set-or-a-property-is-read) says
what a call through a set or a property reads and carries.

## `at`

`at` joins a property with no group-by, so it reads one coarse value once for
each fine label that points at it ([lookups](sets.md#lookups)). One
decision per bus, read by every line that touches the bus, is
`at(decision, by=line[from_bus])`.

## `sum_back`

`sum_back` sums the last `window` positions along a dimension. Use it for a
minimum up time, a rolling budget or a delivery horizon. The dimension
**stays** in the result, and a window of `1` gives `x` itself.

```yaml
dimensions:
  unit: { dtype: str }
  hour: { dtype: int, ordered: true }

parameters:
  min_up: { dims: [unit], dtype: int }

variables:
  started: { dims: [unit, hour], domain: binary }
  on: { dims: [unit, hour], domain: binary }

constraints:
  stays_up_its_own_time:
    dims: [unit, hour]
    expression: sum_back(started, along=hour, window=min_up) <= on

objective: { sense: minimize, expression: sum(on) }
```

A window given as a parameter is `dtype: int`, and does not vary along the
dimension being summed.

`edge=` takes `'wrap'` or nothing, and a number is a load error. Without
`edge=`, a window that reaches past the start of the dimension is **short**,
and no row is lost.

`within=` takes a [partition](sets.md#partitions).

## `shift`

`shift` counts positions in the order of an [ordered](dimensions.md#order)
dimension. `edge=` says what stands where nothing moved in.

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  storage: { dtype: str }
parameters:
  eta: { dims: [storage] }
variables:
  soc: { dims: [snapshot, storage] }
  charge: { dims: [snapshot, storage] }
  discharge: { dims: [snapshot, storage] }
constraints:
  storage_balance:
    dims: [snapshot, storage]
    expression: soc == shift(soc, along=snapshot, offset=1, edge='wrap') + charge * eta - discharge
```

`edge='wrap'` makes the store cyclic: the first snapshot reads the last. Without
`edge=`, the row that the vacated coordinate would feed is not built, so state
the initial condition in an entry of its own ([a rule that differs by
regime](../../howto/regimes.md)).

Two rules hold for `edge=`:

- Over a variable, the only numeric edge is `0`.
- A bare `shift` over an expression with no variable is a load error, and the
  error names the rewrites: `edge='wrap'`, `edge=0`, or `edge=0` together with
  a `where` that excludes the vacated coordinate.

### Translation within groups

`within=` takes a [partition](sets.md#partitions), and the neighbour of a
coordinate is the one before it in its own group, such as a season:

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  season: { dtype: str }
properties:
  snapshot:
    season: season
parameters:
  inflow: { dims: [snapshot] }
variables:
  soc: { dims: [snapshot], bounds: { lower: 0 } }
constraints:
  season_balance:
    dims: [snapshot]
    expression: soc == shift(soc, along=snapshot, offset=1, edge='wrap', within=snapshot[season]) + inflow
objective: { sense: minimize, expression: sum(soc) }
```

Every `edge=` setting then applies one group at a time, and a coordinate in no
group is dropped under every `edge=`.

### A parameter as offset

Use a parameter as offset for a construction lead time, a transit time, or any
delay the data carries as a column:

```yaml
dimensions:
  technology: { dtype: str }
  month: { dtype: int, ordered: true }
parameters:
  lead: { dims: [technology], dtype: int }
  demand: { dims: [technology, month] }
variables:
  order:
    dims: [technology, month]
    bounds: { lower: 0 }
constraints:
  arrives_after_its_lead:
    dims: [technology, month]
    expression: shift(order, along=month, offset=lead, edge=0) >= demand
objective: { sense: minimize, expression: sum(order) }
```

Each of these is a load error:

- The parameter is not `dtype: int`.
- The parameter varies along the dimension being translated.
- The parameter varies over a dimension the shift cannot read. The shift
  reads the dimensions of the shifted expression, and the dimension a
  [`within=`](#translation-within-groups) column groups into: `offset=lead`
  with `lead: {dims: [period]}` under `within=period_of[period]` gives one lag
  per period.

Put the sign in the data: `offset=-lead` is refused.

## Every operator as math

`tools/spec_math.py` generates each row from one spec in
[`examples/operators/`](https://github.com/energy-models/mathspec/tree/main/examples/operators),
and the [typesetter](../typeset.md) prints it. The specs themselves are on
[One construct per spec](../../examples/operators.md).

<!-- operator-math:begin -->
| Operator | Renders as |
|---|---|
| `sum(array)` | $`\sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \le \mathrm{budget}`$ |
| `sum(array, over=dim)` | $`\sum_{g \in \mathcal{G}} p_{t,g} \le \mathrm{limit}_{t} \qquad \forall\, t \in \mathcal{T}`$ |
| `sum(array, over=[a, …])` | $`\sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g,c} \le \mathrm{limit}_{c} \qquad \forall\, c \in \mathcal{C}`$ |
| `sum(array, over=dim, by=subject[p])` | $`\sum_{g \in \mathcal{G} \,:\, \mathrm{bus}(g) = b} p_{t,g} \le \mathrm{limit}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}`$ |
| `sum(array, over=dim, by=subject[p]), joining on the other members` | $`\sum_{g \in \mathcal{G} \,:\, \mathrm{zone}(g,\ e) = z} p_{g,e} \ge \mathrm{demand}_{z,e} \qquad \forall\, z \in \mathcal{Z},\ e \in \mathcal{E}`$ |
| `sum(array, over=[dim, …], by=subject[p, …])` | $`\sum_{g \in \mathcal{G},\ e \in \mathcal{E} \,:\, \mathrm{bus}(g,\ e) = b \wedge \mathrm{technology}(g,\ e) = t} p_{g,e} \le \mathrm{cap}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}`$ |
| `at(array, by=subject[p])` | $`p_{t} \le \mathrm{cap}_{\mathrm{period}(t)} \qquad \forall\, t \in \mathcal{T}`$ |
| `at(array, by=subject[p]), two properties into one dimension` | $`f_{l} \le \mathrm{cap}_{\mathrm{bus0}(l)} \qquad \forall\, l \in \mathcal{L}`$ |
| `shift(array, along=dim, offset=n)` | $`p_{t} \le p_{t - 1} \qquad \forall\, t \in \mathcal{T}`$ |
| `shift(array, along=dim, offset=n, edge='wrap')` | $`p_{t} \le p_{t \ominus 1} \qquad \forall\, t \in \mathcal{T}`$ |
| `shift(array, along=dim, offset=n, edge=v)` | $`p_{t} \le p_{t \boxminus_{0} 1} \qquad \forall\, t \in \mathcal{T}`$ |
| `shift(array, along=dim, offset=p, edge=…)` | $`\mathit{order}_{t,m \boxminus_{0} \mathrm{lead}} \ge \mathrm{demand}_{t,m} \qquad \forall\, t \in \mathcal{T},\ m \in \mathcal{M}`$ |
| `shift(array, along=dim, offset=n, within=subject[p])` | $`p_{t} \le p_{t \ominus^{\mathrm{season}(t)} 1} \qquad \forall\, t \in \mathcal{T}`$ |
| `sum_back(array, along=dim, window=n)` | $`\sum_{h' \in \mathcal{H} \,:\, 0 \le h - h' < 3} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}`$ |
| `sum_back(array, along=dim, window=p)` | $`\sum_{h' \in \mathcal{H} \,:\, 0 \le h - h' < \mathrm{min\_up}} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}`$ |
| `sum_back(array, along=dim, window=p, edge='wrap')` | $`\sum_{h' \in \mathcal{H} \,:\, 0 \le h \ominus h' < \mathrm{min\_up}} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}`$ |
| `sum_back(array, along=dim, window=n, within=subject[p])` | $`\sum_{h' \in \mathcal{H} \,:\, 0 \le h -^{\mathrm{day}(h)} h' < 3} \mathit{started}_{u,h'} \le \mathit{on}_{u,h} \qquad \forall\, u \in \mathcal{U},\ h \in \mathcal{H}`$ |
| `dual(constraint)` | $`\mathit{price}_{t} = \lambda_{\mathrm{balance},t} \qquad \forall\, t \in \mathcal{T}`$ |
<!-- operator-math:end -->

Regenerate with `pixi run python -m tools.spec_math`.

<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Every construct, as math

Look up any construct of the language to see the math that
[the typesetter](typeset.md) prints for it. You can also start from a symbol and
find the construct that printed it.

Each section shows the YAML of one construct, then its equation. Most fragments
come from one test spec,
[`tests/typesetting/golden/model.yaml`](https://github.com/energy-models/mathspec/blob/main/tests/typesetting/golden/model.yaml),
which holds every construct and does not make sense as an optimisation
problem. The curves come from the example specs that their section names.
[Operators](language/operators.md) says what each operator does.

The symbols are **derived** from the names in the file, so you see
$\mathrm{load}_{t}$ rather than $\ell_t$. A
[symbol table](typeset.md#symbol-tables) replaces the symbols and changes
nothing else.

<!-- notation:begin -->
### Legend

A dimension, a set, a property and a parameter declare no equation; what they print is the legend every spec opens with.

```yaml
dimensions:
  snapshot: { dtype: int, ordered: true }
  generator: { dtype: str, ordered: true }
  bus: { dtype: str }
  zone: { dtype: str }
  season: { dtype: str }
  technology: { dtype: str }
  bp: { dtype: int, ordered: true } # the breakpoints every curve below runs through

sets:
  dispatch_pair: { dims: [generator, bus], missing: absent } # a set: the pairs that exist, and the subject of a property below
  generator_snapshot: { dims: [generator, snapshot] } # a set over two dimensions: a call through its property sums one away and joins on the other
  connection: { dims: [generator, bus], missing: absent } # a set with no property: many-to-many, read only by sum with both members named

properties:
  generator:
    fuel: { into: technology, missing: absent } # a property of a dimension: the legend names it after itself, and says a generator may have none
    bus: bus
    technology: technology # with bus, two properties read at once: the call reads their inner join
  bus:
    zone: zone
    area: { into: zone, missing: absent } # a second property into the same dimension, to compare against; a bus may be in no area
  snapshot:
    season: season
    rep: snapshot # a property into its own dimension: the representative snapshot
  generator_snapshot:
    zone: zone
  dispatch_pair:
    area: zone # a property of a set: the legend maps it from the set by name

parameters:
  p_max: { dims: [generator], missing: .inf } # a value: the legend says what a missing row reads as
  p_min: { dims: [generator] }
  cost: { dims: [generator], missing: 0 } # a reading: the legend names it
  load: { dims: [snapshot, bus] }
  is_flexible: { dims: [generator], dtype: bool, missing: false }
  zone_cap: { dims: [zone] }
  tech_cap: { dims: [bus, technology], missing: absent }
  link_eff: { dims: [generator, bus], where: connection, missing: 1 } # a mask: the legend says where it has coordinates, then what a missing row inside them reads as
  min_up: { dims: [generator], dtype: int }
  eta: { dims: [generator] } # a Greek name that is *given*, so the rule wins and it prints as the word
  lead: { dims: [generator], dtype: int }
  budget: { dims: [] } # scalar: the legend says so rather than printing an empty product
  growth: { dims: [] } # the base of a power; the exponent is `lead`, a column
  bp_x: { dims: [generator, bp], missing: 0 } # the x-axis of every curve below, and what a derived mask is read from
  bp_y: { dims: [generator, bp], missing: 0 }
  bp_heat: { dims: [generator, bp] }
  bp_run: { dims: [generator, bp], dtype: bool } # how far each curve runs, so a piecewise entry has a mask to print
```

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` (`int` coordinates) with $`\mathrm{generator\_snapshot} \subseteq \mathcal{G} \times \mathcal{T},\ \mathrm{season}: \mathcal{T} \to \mathcal{S},\ \mathrm{rep}: \mathcal{T} \to \mathcal{T},\ \mathrm{zone}: \mathrm{generator\_snapshot} \to \mathcal{Z}`$ |
| $`\mathcal{G}`$ | index $`g`$ — `generator` with $`\mathrm{dispatch\_pair} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{generator\_snapshot} \subseteq \mathcal{G} \times \mathcal{T},\ \mathrm{connection} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{fuel}: \mathcal{G} \to \mathcal{E},\ \mathrm{bus}: \mathcal{G} \to \mathcal{B},\ \mathrm{technology}: \mathcal{G} \to \mathcal{E},\ \mathrm{zone}: \mathrm{generator\_snapshot} \to \mathcal{Z},\ \mathrm{area}: \mathrm{dispatch\_pair} \to \mathcal{Z}`$, `dispatch_pair` is `absent` where the data has no row, `connection` is `absent` where the data has no row, `generator[fuel]` is `absent` where the data has no row |
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{dispatch\_pair} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{connection} \subseteq \mathcal{G} \times \mathcal{B},\ \mathrm{bus}: \mathcal{G} \to \mathcal{B},\ \mathrm{zone}: \mathcal{B} \to \mathcal{Z},\ \mathrm{area}: \mathcal{B} \to \mathcal{Z},\ \mathrm{area}: \mathrm{dispatch\_pair} \to \mathcal{Z}`$, `dispatch_pair` is `absent` where the data has no row, `connection` is `absent` where the data has no row, `bus[area]` is `absent` where the data has no row |
| $`\mathcal{Z}`$ | index $`z`$ — `zone` with $`\mathrm{zone}: \mathcal{B} \to \mathcal{Z},\ \mathrm{area}: \mathcal{B} \to \mathcal{Z},\ \mathrm{zone}: \mathrm{generator\_snapshot} \to \mathcal{Z},\ \mathrm{area}: \mathrm{dispatch\_pair} \to \mathcal{Z}`$, `bus[area]` is `absent` where the data has no row |
| $`\mathcal{S}`$ | index $`s`$ — `season` with $`\mathrm{season}: \mathcal{T} \to \mathcal{S}`$ |
| $`\mathcal{E}`$ | index $`e`$ — `technology` with $`\mathrm{fuel}: \mathcal{G} \to \mathcal{E},\ \mathrm{technology}: \mathcal{G} \to \mathcal{E}`$, `generator[fuel]` is `absent` where the data has no row |
| $`\mathcal{A}`$ | index $`a`$ — `bp` |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{p}^{\mathrm{max}}`$ | `p_max` over $`\mathcal{G}`$, $`\infty`$ where the data has no row |
| $`\mathrm{p}^{\mathrm{min}}`$ | `p_min` over $`\mathcal{G}`$ |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{G}`$, $`0`$ where the data has no row |
| $`\mathrm{load}`$ | `load` over $`\mathcal{T} \times \mathcal{B}`$ |
| $`\mathrm{is\_flexible}`$ | `is_flexible` over $`\mathcal{G}`$, `false` where the data has no row |
| $`\mathrm{zone\_cap}`$ | `zone_cap` over $`\mathcal{Z}`$ |
| $`\mathrm{tech\_cap}`$ | `tech_cap` over $`\mathcal{B} \times \mathcal{E}`$, `absent` where the data has no row |
| $`\mathrm{link\_eff}`$ | `link_eff` over $`\mathcal{G} \times \mathcal{B}`$, only where $`\left( g,\ b \right) \in \mathrm{connection}`$, $`1`$ where the data has no row |
| $`\mathrm{min\_up}`$ | `min_up` over $`\mathcal{G}`$ |
| $`\mathrm{eta}`$ | `eta` over $`\mathcal{G}`$ |
| $`\mathrm{lead}`$ | `lead` over $`\mathcal{G}`$ |
| $`\mathrm{budget}`$ | `budget` (scalar) |
| $`\mathrm{growth}`$ | `growth` (scalar) |
| $`\mathrm{bp\_x}`$ | `bp_x` over $`\mathcal{G} \times \mathcal{A}`$, $`0`$ where the data has no row |
| $`\mathrm{bp\_y}`$ | `bp_y` over $`\mathcal{G} \times \mathcal{A}`$, $`0`$ where the data has no row |
| $`\mathrm{bp\_heat}`$ | `bp_heat` over $`\mathcal{G} \times \mathcal{A}`$ |
| $`\mathrm{bp\_run}`$ | `bp_run` over $`\mathcal{G} \times \mathcal{A}`$ |

#### Conditions

| Symbol | Meaning |
|---|---|
| $`\mathrm{dispatchable}`$ | `dispatchable` over $`\mathcal{G}`$ — a unit that dispatches and cannot be turned down |
| $`\mathrm{priced\_dispatch}`$ | `priced_dispatch` over $`\mathcal{G}`$ |

#### Variables

| Symbol | Meaning |
|---|---|
| $`p`$ | `p` over $`\mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{spill}`$ | `spill` over $`\mathcal{T}`$ |
| $`\mathit{slack}`$ | `slack` over $`\mathcal{T}`$ |
| $`\theta`$ | `theta` over $`\mathcal{B}`$ |
| $`\mathit{on}`$ | `on` over $`\mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{units}`$ | `units` over $`\mathcal{G}`$ |
| $`\mathit{spare}`$ | `spare` over $`\mathcal{G}`$ |
| $`\mathit{reserve}`$ | `reserve` (scalar) |
| $`\mathit{headroom}`$ | `headroom` (scalar), $`0`$ where the mask leaves it out |
| $`\mathit{weight}`$ | `weight` over $`\mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{fuel}`$ | `fuel` over $`\mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{heat}`$ | `heat` over $`\mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{op\_cost}`$ | `op_cost` over $`\mathcal{T} \times \mathcal{G}`$ |
| $`\mathit{warm}`$ | `warm` over $`\mathcal{T} \times \mathcal{G}`$ |

#### Expressions

| Symbol | Meaning |
|---|---|
| $`\mathrm{spend}^{\mathrm{cap}}`$ | `spend_cap` over $`\mathcal{G}`$ |
| $`\mathit{spend}`$ | `spend` over $`\mathcal{T}`$ — what a snapshot's dispatch costs |
| $`\mathrm{rating}`$ | `rating` over $`\mathcal{G} \times \mathcal{T}`$ |
| $`\mathit{lcoe}`$ | `lcoe` (scalar) |
| $`\mathit{net}`$ | `net` over $`\mathcal{T}`$ — what a snapshot spills, less what it lacks |
| $`\mathit{marginal\_price}`$ | `marginal_price` over $`\mathcal{B} \times \mathcal{T}`$ |
| $`\mathrm{startup\_cost}`$ | `startup_cost` over $`\mathcal{T} \times \mathcal{G}`$ — what starting a unit in this snapshot costs, which the horizon's edge changes |

#### Notation

| Symbol | Meaning |
|---|---|
| $`t \ominus k`$ | `edge='wrap'` — $`t-k`$, cyclic |
| $`t \boxminus_{v} k`$ | `edge=v` — $`t-k`$, and $`v`$ past the edge |
| $`t \ominus^{\mathrm{property}(t)} k`$ | `within=subject[...]` — $`t-k`$ inside the group of $`t`$ |
| $`\mathrm{pos}(t)`$ | `position()` — the position of $`t`$, counted from $`0`$; $`t`$ is the label |
| $`\mathrm{pos}_{\mathrm{property}(t)}(t)`$ | `position(within=subject[...])` — the position of $`t`$ inside its group |
| $`\lvert \mathcal{T} \rvert`$ | the size of $`\mathcal{T}`$; $`\lvert \mathcal{T} \rvert - 1`$ is the last position |

### Variable domains

#### Lower and upper bounds

both bounds, and a where with all three connectives

```yaml
variables:
  p:
    dims: [snapshot, generator]
    where: "p_max > 0 AND NOT is_flexible OR p_min > 0"
    bounds: { lower: p_min, upper: p_max }
```

```math
\mathrm{p}^{\mathrm{min}}_{g} \le p_{t,g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{p}^{\mathrm{max}}_{g} > 0 \wedge \neg \mathrm{is\_flexible}_{g} \vee \mathrm{p}^{\mathrm{min}}_{g} > 0
```

#### Lower bound only

```yaml
variables:
  spill:
    dims: [snapshot]
    bounds: { lower: 0 }
```

```math
\mathit{spill}_{t} \ge 0 \qquad \forall\, t \in \mathcal{T}
```

#### Upper bound only

```yaml
variables:
  slack:
    dims: [snapshot]
    bounds: { upper: 100 }
```

```math
\mathit{slack}_{t} \le 100 \qquad \forall\, t \in \mathcal{T}
```

#### Unbounded variable

```yaml
variables:
  theta:
    dims: [bus]
```

```math
\theta_{b} \in \mathbb{R} \qquad \forall\, b \in \mathcal{B}
```

#### Binary domain

a binary domain, which is a set rather than a pair of bounds

```yaml
variables:
  on:
    dims: [snapshot, generator]
    domain: binary
```

```math
\mathit{on}_{t,g} \in \{0, 1\} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Bounded integer domain

an integer domain, which is both: bounds, and where the values live

```yaml
variables:
  units:
    dims: [generator]
    domain: integer
    bounds: { lower: 0, upper: 10 }
```

```math
0 \le \mathit{units}_{g} \le 10, \mathit{units}_{g} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G}
```

#### Unbounded integer domain

integer with neither bound: the domain is the whole line

```yaml
variables:
  spare:
    dims: [generator]
    domain: integer
```

```math
\mathit{spare}_{g} \in \mathbb{Z} \qquad \forall\, g \in \mathcal{G}
```

#### Scalar variable

an empty dims: a scalar entry, whose line carries no quantifier

```yaml
variables:
  reserve:
    dims: []
    bounds: { lower: 0 }
```

```math
\mathit{reserve} \ge 0
```

#### Scalar variable with a condition

scalar too, but masked, so the condition stands with no set beside it; 0, so the legend names the value

```yaml
variables:
  headroom:
    dims: []
    where: "budget"
    missing: 0
    bounds: { lower: 0 }
```

```math
\mathit{headroom} \ge 0 \qquad \text{where } \mathrm{budget} \text{ is defined}
```

#### Variable in a special ordered set

the family a sos runs along

```yaml
variables:
  weight:
    dims: [snapshot, generator]
    bounds: { lower: 0, upper: 1 }
```

```math
0 \le \mathit{weight}_{t,g} \le 1 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Second axis of a curve

a curve's second axis

```yaml
variables:
  fuel:
    dims: [snapshot, generator]
    bounds: { lower: 0 }
```

```math
\mathit{fuel}_{t,g} \ge 0 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Third axis of a curve

its third, so one curve ties three expressions

```yaml
variables:
  heat:
    dims: [snapshot, generator]
    bounds: { lower: 0 }
```

```math
\mathit{heat}_{t,g} \ge 0 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Variable bounded by a curve

bounded by a curve rather than pinned to it

```yaml
variables:
  op_cost:
    dims: [snapshot, generator]
    bounds: { lower: 0 }
```

```math
\mathit{op\_cost}_{t,g} \ge 0 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Binary variable with a condition

a gate not every unit has, so the curve it gates is ungated where it does not exist

```yaml
variables:
  warm:
    dims: [snapshot, generator]
    domain: binary
    where: "is_flexible"
```

```math
\mathit{warm}_{t,g} \in \{0, 1\} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{is\_flexible}_{g}
```

### Objective

#### Products and powers in the objective

a sense, a product of two variables, a power over two parameters, a power of one of those, and the summations a scalar objective spells out beside two scalar terms

```yaml
objective:
  sense: maximize
  expression: sum(p * cost) + sum(p * p * cost) + sum(p * cost * growth ** lead) + sum(p * (growth ** lead) ** 2) + sum(p * p_max) - reserve + -headroom
```

```math
\max \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot \mathrm{cost}_{g} + \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot p_{t,g} \cdot \mathrm{cost}_{g} + \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot \mathrm{cost}_{g} \cdot \mathrm{growth}^{\mathrm{lead}_{g}} + \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot \left( \mathrm{growth}^{\mathrm{lead}_{g}} \right)^{2} + \sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot \mathrm{p}^{\mathrm{max}}_{g} - \mathit{reserve} - \mathit{headroom}
```

### Sets and properties

#### Sum through a property

```yaml
constraints:
  balance:
    dims: [snapshot, bus]
    expression: sum(p, over=generator, by=generator[bus]) + spill - slack == load
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{bus}(g) = b} p_{t,g} + \mathit{spill}_{t} - \mathit{slack}_{t} = \mathrm{load}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
```

#### Sum over every dimension

a sum naming no dim, whose domain is the one place the dims it took are said

```yaml
constraints:
  total:
    dims: []
    expression: sum(p) <= budget
```

```math
\sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \le \mathrm{budget}
```

#### `at` through a property

at(), which re-indexes through a property instead of an offset

```yaml
constraints:
  lookup:
    dims: [snapshot, bus]
    expression: spill <= at(zone_cap, by=bus[zone])
```

```math
\mathit{spill}_{t} \le \mathrm{zone\_cap}_{\mathrm{zone}(b)} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
```

#### Sum into two properties

one table read to two value columns: the domain carries a condition per column

```yaml
constraints:
  grouped_once:
    dims: [snapshot, bus, technology]
    expression: sum(p, over=generator, by=generator[bus, technology]) <= tech_cap
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{bus}(g) = b \wedge \mathrm{technology}(g) = e} p_{t,g} \le \mathrm{tech\_cap}_{b,e} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B},\ e \in \mathcal{E}
```

#### `at` through two properties

the same table joined the other way, reading one slot through two columns

```yaml
constraints:
  looked_up_once:
    dims: [generator]
    expression: units <= at(tech_cap, by=generator[bus, technology])
```

```math
\mathit{units}_{g} \le \mathrm{tech\_cap}_{\mathrm{bus}(g),\mathrm{technology}(g)} \qquad \forall\, g \in \mathcal{G}
```

#### Shift within one of two properties

a partition grouped by one named value column of a two-value table, and a position within both

```yaml
constraints:
  within_bus:
    dims: [generator]
    where: "position(generator, within=generator[bus, technology]) == 0"
    expression: units <= shift(units, along=generator, offset=1, edge=0, within=generator[bus])
```

```math
\mathit{units}_{g} \le \mathit{units}_{g \boxminus_{0}^{\mathrm{bus}(g)} 1} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{pos}_{\left( \mathrm{bus}(g),\ \mathrm{technology}(g) \right)}(g) = 0
```

#### Sum through a set

a sum through a set: the domain is a row of the set rather than a function's value

```yaml
constraints:
  relational:
    dims: [snapshot, bus]
    expression: sum(p, over=generator, by=connection[bus]) <= load
```

```math
\sum_{g \in \mathcal{G} \,:\, \left( g,\ b \right) \in \mathrm{connection}} p_{t,g} \le \mathrm{load}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
```

#### Set as a condition

a set as a where: the row of the frame has to be a row of the set

```yaml
constraints:
  connected:
    dims: [snapshot, generator, bus]
    where: "connection"
    expression: p <= load
```

```math
p_{t,g} \le \mathrm{load}_{t,b} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \left( g,\ b \right) \in \mathrm{connection}
```

#### Property into its own dimension

a map into its own dimension, read both ways: the frame is unchanged and the index is primed

```yaml
constraints:
  representative:
    dims: [snapshot]
    expression: sum(spill, over=snapshot, by=snapshot[rep]) <= at(spill, by=snapshot[rep])
```

```math
\sum_{t' \in \mathcal{T} \,:\, \mathrm{rep}(t') = t} \mathit{spill}_{t'} \le \mathit{spill}_{\mathrm{rep}(t)} \qquad \forall\, t \in \mathcal{T}
```

#### Sum through a property of a dimension

a sum through a property of a dimension, read as the property's own name

```yaml
constraints:
  by_fuel:
    dims: [snapshot, technology]
    expression: sum(p, over=generator, by=generator[fuel]) <= budget
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{fuel}(g) = e} p_{t,g} \le \mathrm{budget} \qquad \forall\, t \in \mathcal{T},\ e \in \mathcal{E}
```

#### Sum through a property of a set

a sum through a property of a set, over both of its members

```yaml
constraints:
  by_area:
    dims: [snapshot, zone]
    expression: sum(p * link_eff, over=[generator, bus], by=dispatch_pair[area]) <= zone_cap
```

```math
\sum_{g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \mathrm{area}(g,\ b) = z} p_{t,g} \cdot \mathrm{link\_eff}_{g,b} \le \mathrm{zone\_cap}_{z} \qquad \forall\, t \in \mathcal{T},\ z \in \mathcal{Z}
```

#### Property as a condition

a property alone as a where: the row has it

```yaml
constraints:
  fuelled:
    dims: [snapshot, generator]
    where: "generator[fuel]"
    expression: p <= budget
```

```math
p_{t,g} \le \mathrm{budget} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{fuel}(g) \text{ is defined}
```

#### Sum over one member of a set, through its property

a grouping through a two-key map, summing one key away: the condition reads the other, and the row keeps it

```yaml
constraints:
  zonal:
    dims: [snapshot, zone]
    expression: sum(p, over=generator, by=generator_snapshot[zone]) <= zone_cap
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{zone}(g,\ t) = z} p_{t,g} \le \mathrm{zone\_cap}_{z} \qquad \forall\, t \in \mathcal{T},\ z \in \mathcal{Z}
```

#### Sum over the other member of a set

the same table summing its other key away

```yaml
constraints:
  zonal_history:
    dims: [generator, zone]
    expression: sum(p, over=snapshot, by=generator_snapshot[zone]) <= zone_cap
```

```math
\sum_{t \in \mathcal{T} \,:\, \mathrm{zone}(g,\ t) = z} p_{t,g} \le \mathrm{zone\_cap}_{z} \qquad \forall\, g \in \mathcal{G},\ z \in \mathcal{Z}
```

#### Sum between the two members of a set

the same table read between its two key columns: no value column is read, so the domain asks only that the row is there

```yaml
constraints:
  zonal_membership:
    dims: [snapshot]
    expression: sum(units, over=generator, by=generator_snapshot[snapshot]) <= budget
```

```math
\sum_{g \in \mathcal{G} \,:\, \left( g,\ t \right) \in \mathrm{generator\_snapshot}} \mathit{units}_{g} \le \mathrm{budget} \qquad \forall\, t \in \mathcal{T}
```

#### `at` through a property of a set

the same table joined the other way, reading the slot the row's own snapshot puts the generator in

```yaml
constraints:
  zonal_lookup:
    dims: [snapshot, generator]
    where: "generator_snapshot[zone] == 'north' AND position(generator, within=generator_snapshot[zone]) == 0"
    expression: p <= at(spill * zone_cap, by=generator_snapshot[zone])
```

```math
p_{t,g} \le \mathit{spill}_{t} \cdot \mathrm{zone\_cap}_{\mathrm{zone}(g,\ t)} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{zone}(g,\ t) = \text{'}\mathrm{north}\text{'} \wedge \mathrm{pos}_{\mathrm{zone}(g,\ t)}(g) = 0
```

### Arithmetic and literals

#### Signs, division and number literals

division, both unary signs, a sign beside a sign, floats with and without an exponent, bracketing

```yaml
constraints:
  arithmetic:
    dims: [snapshot]
    expression: >-
      sum(p / 2 + -cost - -1e-5 * p + 2.5e-7 * cost + 0.5 * p, over=generator)
      >= -sum(+p, over=generator) * -3
```

```math
\sum_{g \in \mathcal{G}} \left( \frac{p_{t,g}}{2} - \mathrm{cost}_{g} + 10^{-5} \cdot p_{t,g} + 2.5 \times 10^{-7} \cdot \mathrm{cost}_{g} + 0.5 \cdot p_{t,g} \right) \ge -\left( \sum_{g \in \mathcal{G}} p_{t,g} \right) \cdot \left( -3 \right) \qquad \forall\, t \in \mathcal{T}
```

#### Greek parameter name

a Greek-named parameter, which is given — so the convention wins and it prints as the word

```yaml
constraints:
  efficiency:
    dims: [snapshot, generator]
    expression: p <= eta * p_max
```

```math
p_{t,g} \le \mathrm{eta}_{g} \cdot \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Infinity literal

the infinity literal, which is the one way infinity prints

```yaml
constraints:
  ceiling:
    dims: [bus]
    expression: theta <= inf
```

```math
\theta_{b} \le \infty \qquad \forall\, b \in \mathcal{B}
```

### Named expressions

#### Plain expression in a constraint

names the plain expression: its symbol prints here, its definition once below

```yaml
constraints:
  budgeted:
    dims: [snapshot]
    expression: spend <= budget
```

```math
\mathit{spend}_{t} \le \mathrm{budget} \qquad \forall\, t \in \mathcal{T}
```

#### Signed sum substituted into a plus

names the signed sum on the right of a plus: inlined, its minus prints as a subtraction

```yaml
constraints:
  netted:
    dims: [snapshot, bus]
    expression: sum(p, over=generator, by=generator[bus]) + net == load
```

```math
\sum_{g \in \mathcal{G} \,:\, \mathrm{bus}(g) = b} p_{t,g} + \mathit{net}_{t} = \mathrm{load}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B}
```

#### Cased expression in a constraint

names the cased expression: its symbol prints here, its block once below

```yaml
constraints:
  starts:
    dims: [snapshot, generator]
    expression: p <= startup_cost
```

```math
p_{t,g} \le \mathrm{startup\_cost}_{t,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Expression with a declared frame in a constraint

names the expression with declared dims, read in the row's own order

```yaml
constraints:
  under_rating:
    dims: [snapshot, generator]
    expression: p <= rating
```

```math
p_{t,g} \le \mathrm{rating}_{g,t} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Plain named expression

a plain named expression: its symbol prints where it is used, its body once as a definition

```yaml
expressions:
  spend:
    expression: sum(p * cost, over=generator)
```

```math
\mathit{spend}_{t} = \sum_{g \in \mathcal{G}} p_{t,g} \cdot \mathrm{cost}_{g} \qquad \forall\, t \in \mathcal{T}
```

#### Named expression with a declared frame

dims declared in an order of their own, each one the expression is indexed over

```yaml
expressions:
  rating:
    dims: [generator, snapshot]
    expression: eta * p_max * sum(load, over=bus)
```

```math
\mathrm{rating}_{g,t} = \mathrm{eta}_{g} \cdot \mathrm{p}^{\mathrm{max}}_{g} \cdot \left( \sum_{b \in \mathcal{B}} \mathrm{load}_{t,b} \right) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

#### Plain expression that is a signed sum

a plain expression that opens with a minus

```yaml
expressions:
  net:
    expression: -spill + slack
```

```math
\mathit{net}_{t} = -\mathit{spill}_{t} + \mathit{slack}_{t} \qquad \forall\, t \in \mathcal{T}
```

#### Expression defined by cases

a quantity defined by region: no two cases overlap, and `otherwise` is the rest

```yaml
expressions:
  startup_cost:
    dims: [snapshot, generator]
    cases:
      opening: { when: "position(snapshot) == 0", expression: cost }
      winter: { when: "position(snapshot) > 0 and snapshot[season] == 'winter'", expression: cost * 2 }
    otherwise: 0
```

```math
\mathrm{startup\_cost}_{t,g} = \begin{cases} \mathrm{cost}_{g} & \text{if } \mathrm{pos}(t) = 0 \\ \mathrm{cost}_{g} \cdot 2 & \text{if } \mathrm{pos}(t) > 0 \wedge \mathrm{season}(t) = \text{'}\mathrm{winter}\text{'} \\ 0 & \text{otherwise} \end{cases} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Data-only expression

a data-only entry, so a where may compare it

```yaml
expressions:
  spend_cap: cost * 2
```

```math
\mathrm{spend}^{\mathrm{cap}}_{g} = \mathrm{cost}_{g} \cdot 2 \qquad \forall\, g \in \mathcal{G}
```

#### Named expression in a condition

an expressions: entry on a side, read by the name the file gave it

```yaml
constraints:
  capped:
    dims: [snapshot, generator]
    where: "spend_cap > 0 OR NOT is_flexible"
    expression: p <= p_max
```

```math
p_{t,g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{spend}^{\mathrm{cap}}_{g} > 0 \vee \neg \mathrm{is\_flexible}_{g}
```

#### Reported expression

nothing in the math reads it, so its divisor may carry a variable

```yaml
expressions:
  lcoe: sum(p * cost) / sum(p)
```

```math
\mathit{lcoe} = \frac{\sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \cdot \mathrm{cost}_{g}}{\sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g}}
```

#### Dual of a constraint

the row dual of a constraint, the one builtin only an entry the math never reads may call

```yaml
expressions:
  marginal_price: dual(balance)
```

```math
\mathit{marginal\_price}_{b,t} = \lambda_{\mathrm{balance},t,b} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

### Named conditions

#### Named condition

a named condition with its words: a use prints the symbol over the dims its condition reads, the condition prints once

```yaml
conditions:
  dispatchable:
    condition: "p_max > 0 AND NOT is_flexible"
```

```math
\mathrm{dispatchable}_{g} \iff \mathrm{p}^{\mathrm{max}}_{g} > 0 \wedge \neg \mathrm{is\_flexible}_{g} \qquad \forall\, g \in \mathcal{G}
```

#### Condition that reads a condition

the one-line form, reading another mask and a data-only entry

```yaml
conditions:
  priced_dispatch: "dispatchable AND spend_cap > 0"
```

```math
\mathrm{priced\_dispatch}_{g} \iff \mathrm{dispatchable}_{g} \wedge \mathrm{spend}^{\mathrm{cap}}_{g} > 0 \qquad \forall\, g \in \mathcal{G}
```

#### Named condition in a condition

a mask as the where, beside a condition of the constraint's own

```yaml
constraints:
  masked:
    dims: [snapshot, generator]
    where: "priced_dispatch AND position(snapshot) > 0"
    expression: p <= p_max
```

```math
p_{t,g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{priced\_dispatch}_{g} \wedge \mathrm{pos}(t) > 0
```

### Shifts

#### Cyclic and acyclic shift

roll (cyclic) and shift (acyclic) in one equation

```yaml
constraints:
  ramp:
    dims: [snapshot, generator]
    expression: p - shift(p, along=snapshot, offset=1, edge='wrap') <= shift(p, along=snapshot, offset=1) + p_max
```

```math
p_{t,g} - p_{t \ominus 1,g} \le p_{t - 1,g} + \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Filled and forward shifts

the two translations `ramp` leaves out: a fill, and forwards

```yaml
constraints:
  edges:
    dims: [snapshot, generator]
    expression: >-
      shift(p, along=snapshot, offset=1, edge=0)
      <= shift(p, along=snapshot, offset=-1, edge=0) + p_max
```

```math
p_{t \boxminus_{0} 1,g} \le p_{t \boxplus_{0} 1,g} + \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Cyclic forward shift

the cyclic translation forwards, which is a fourth symbol again

```yaml
constraints:
  ahead:
    dims: [snapshot, generator]
    expression: p <= shift(p, along=snapshot, offset=-1, edge='wrap')
```

```math
p_{t,g} \le p_{t \oplus 1,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Composed shifts

two steps of one policy are one step; a zero step is none at all

```yaml
constraints:
  composed:
    dims: [snapshot, generator]
    expression: shift(shift(p, along=snapshot, offset=1), along=snapshot, offset=1) <= shift(p_max, along=generator, offset=0)
```

```math
p_{t - 2,g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Nested shifts that do not compose

a named offset under a numbered one stays two steps, not their sum

```yaml
constraints:
  uncomposed:
    dims: [snapshot, generator]
    expression: shift(shift(p, along=snapshot, offset=lead, edge=0), along=snapshot, offset=1) <= p_max
```

```math
p_{\left( t - 1 \right) \boxminus_{0} \mathrm{lead},g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Shift along two dimensions

two dimensions translated at one leaf, each with its own policy

```yaml
constraints:
  crossed:
    dims: [snapshot, generator]
    expression: shift(shift(p, along=snapshot, offset=1, edge='wrap'), along=generator, offset=-1) <= p_max
```

```math
p_{t \ominus 1,g + 1} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Shift by a parameter offset

an offset the data carries, so it prints as a symbol rather than a number

```yaml
constraints:
  lead_time:
    dims: [snapshot, generator]
    expression: shift(p, along=snapshot, offset=lead, edge=0) <= p_max
```

```math
p_{t \boxminus_{0} \mathrm{lead},g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Cyclic shift within a group

a translation partitioned by a property: the group rides on the operator

```yaml
constraints:
  in_season:
    dims: [snapshot, generator]
    expression: p <= shift(p, along=snapshot, offset=1, edge='wrap', within=snapshot[season])
```

```math
p_{t,g} \le p_{t \ominus^{\mathrm{season}(t)} 1,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Filled shift within a group

the same group, with a fill: each season's opening row is kept and given a zero

```yaml
constraints:
  held_in_season:
    dims: [snapshot, generator]
    expression: p <= shift(p, along=snapshot, offset=1, edge=0, within=snapshot[season])
```

```math
p_{t,g} \le p_{t \boxminus_{0}^{\mathrm{season}(t)} 1,g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

### Trailing windows

#### Window of fixed width

a trailing window of fixed width

```yaml
constraints:
  window:
    dims: [snapshot, generator]
    expression: sum_back(on, along=snapshot, window=3) <= units
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t - t' < 3} \mathit{on}_{t',g} \le \mathit{units}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Window with a parameter width

the same window, its width in the data and its edge wrapped

```yaml
constraints:
  history:
    dims: [snapshot, generator]
    expression: sum_back(on, along=snapshot, window=min_up, edge='wrap') <= units
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t \ominus t' < \mathrm{min\_up}} \mathit{on}_{t',g} \le \mathit{units}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

#### Window within a group

a window partitioned by a property: the group rides on the operator

```yaml
constraints:
  seasonal_window:
    dims: [snapshot, generator]
    expression: sum_back(on, along=snapshot, window=3, within=snapshot[season]) <= units
```

```math
\sum_{t' \in \mathcal{T} \,:\, 0 \le t -^{\mathrm{season}(t)} t' < 3} \mathit{on}_{t',g} \le \mathit{units}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

### Piecewise curves

A curve prints as the curve it states, over the frame the entry builds one per coordinate of, and its expansion prints the rows that curve stands for. One row per `method:`, each from the spec named under it, so the symbols in this section are that spec's.

#### Adjacency method

`method: adjacency` — a binary per segment, and a row making the two nonzero weights neighbours, in `examples/ports/transport_pwl.yaml`.

Rendered with the sidecar symbol table `examples/symbols/transport_pwl.yaml`, which is what the breakpoints print as:

```yaml
notation: latex

names:
  economies_of_scale_lam: "\\lambda"
  economies_of_scale_seg: "\\delta"
  bp_x: "\\mathrm{x}"
  bp_y: "\\mathrm{y}"
```

```yaml
piecewise:
  economies_of_scale:
    over: bp
    links:
      - [shipment, bp_x]
      - [scaled, bp_y]
```

```math
\left( \mathit{shipment}_{p,m},\ \mathit{scaled}_{p,m} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}_{b},\ \mathrm{y}_{b}) \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

Written out by `spec.expand()`:

```math
0 \le \lambda_{m,p,b} \le 1 \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P},\ b \in \mathcal{B}
```

```math
\delta_{m,p,b} \in \{0, 1\} \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P},\ b \in \mathcal{B}
```

```math
\sum_{b \in \mathcal{B}} \lambda_{m,p,b} = 1 \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\mathit{shipment}_{p,m} = \sum_{b \in \mathcal{B}} \lambda_{m,p,b} \cdot \mathrm{x}_{b} \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\mathit{scaled}_{p,m} = \sum_{b \in \mathcal{B}} \lambda_{m,p,b} \cdot \mathrm{y}_{b} \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\sum_{b \in \mathcal{B}} \delta_{m,p,b} \le 1 \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P}
```

```math
\lambda_{m,p,b} \le \delta_{m,p,b} + \delta_{m,p,b \boxminus_{0} 1} \qquad \forall\, m \in \mathcal{M},\ p \in \mathcal{P},\ b \in \mathcal{B}
```

```math
\mathrm{x}_{b} \text{ is defined} \wedge \mathrm{y}_{b} \text{ is defined} \qquad \forall\, b \in \mathcal{B}
```

#### SOS2 method

`method: sos2` — the same weights, restricted by a set the solver branches on (the sos rules), in `examples/sos.yaml`.

Rendered with the sidecar symbol table `examples/symbols/sos.yaml`, which is what the breakpoints print as:

```yaml
notation: latex

names:
  cost_curve_lam: "\\lambda"
  bp_x: "\\mathrm{x}"
  bp_y: "\\mathrm{y}"
```

```yaml
piecewise:
  cost_curve:
    over: bp
    links:
      - [dispatch, bp_x]
      - [op_cost, bp_y]
    method: sos2
```

```math
\left( \mathit{dispatch}_{t,g},\ \mathit{op\_cost}_{t,g} \right) \in \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}_{g,b},\ \mathrm{y}_{g,b}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

Written out by `spec.expand()`:

```math
0 \le \lambda_{g,t,b} \le 1 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T},\ b \in \mathcal{B}
```

```math
\sum_{b \in \mathcal{B}} \lambda_{g,t,b} = 1 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathit{dispatch}_{t,g} = \sum_{b \in \mathcal{B}} \lambda_{g,t,b} \cdot \mathrm{x}_{g,b} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathit{op\_cost}_{t,g} = \sum_{b \in \mathcal{B}} \lambda_{g,t,b} \cdot \mathrm{y}_{g,b} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\left( \lambda_{g,t,b} \right)_{b \in \mathcal{B}} \in \mathrm{SOS}2 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathrm{x}_{g,b} \text{ is defined} \wedge \mathrm{y}_{g,b} \text{ is defined} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B}
```

#### Convex method

`method: convex` — nothing, so the weights range over the hull, which is a pure LP, in `examples/piecewise.yaml`.

Rendered with the sidecar symbol table `examples/symbols/piecewise.yaml`, which is what the breakpoints print as:

```yaml
notation: latex

names:
  cost_curve_lam: "\\lambda"
  bp_x: "\\mathrm{x}"
  bp_y: "\\mathrm{y}"
```

```yaml
piecewise:
  cost_curve:
    over: bp
    links:
      - [dispatch, bp_x]
      - [op_cost, bp_y]
    method: convex
```

```math
\left( \mathit{dispatch}_{t,g},\ \mathit{op\_cost}_{t,g} \right) \in \mathrm{conv}_{b \in \mathcal{B}}(\mathrm{x}_{g,b},\ \mathrm{y}_{g,b}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

Written out by `spec.expand()`:

```math
0 \le \lambda_{g,t,b} \le 1 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T},\ b \in \mathcal{B}
```

```math
\sum_{b \in \mathcal{B}} \lambda_{g,t,b} = 1 \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathit{dispatch}_{t,g} = \sum_{b \in \mathcal{B}} \lambda_{g,t,b} \cdot \mathrm{x}_{g,b} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathit{op\_cost}_{t,g} = \sum_{b \in \mathcal{B}} \lambda_{g,t,b} \cdot \mathrm{y}_{g,b} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

```math
\mathrm{x}_{g,b} \text{ is defined} \wedge \mathrm{y}_{g,b} \text{ is defined} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B}
```

```math
\mathrm{x}_{g,b \boxminus_{0} 1} < \mathrm{x}_{g,b} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) > 0
```

```math
\lvert \{ b \in \mathcal{B} \,:\, \left( \mathrm{y}_{g,b} - \mathrm{y}_{g,b \boxminus_{0} 1} \right) \cdot \left( \mathrm{x}_{g,b \boxplus_{0} 1} - \mathrm{x}_{g,b} \right) > \left( \mathrm{y}_{g,b \boxplus_{0} 1} - \mathrm{y}_{g,b} \right) \cdot \left( \mathrm{x}_{g,b} - \mathrm{x}_{g,b \boxminus_{0} 1} \right) \wedge \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1 \} \rvert = 0 \vee \lvert \{ b \in \mathcal{B} \,:\, \left( \mathrm{y}_{g,b} - \mathrm{y}_{g,b \boxminus_{0} 1} \right) \cdot \left( \mathrm{x}_{g,b \boxplus_{0} 1} - \mathrm{x}_{g,b} \right) < \left( \mathrm{y}_{g,b \boxplus_{0} 1} - \mathrm{y}_{g,b} \right) \cdot \left( \mathrm{x}_{g,b} - \mathrm{x}_{g,b \boxminus_{0} 1} \right) \wedge \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1 \} \rvert = 0 \qquad \forall\, g \in \mathcal{G}
```

#### LP method

`method: lp` — no weights, but one row per segment line, plus the two rows holding the domain, in `examples/piecewise_lp.yaml`.

Rendered with the sidecar symbol table `examples/symbols/piecewise_lp.yaml`, which is what the breakpoints print as:

```yaml
notation: latex

names:
  bp_x: "\\mathrm{x}"
  bp_y: "\\mathrm{y}"
```

```yaml
piecewise:
  cost_curve:
    over: bp
    links:
      - [dispatch, bp_x]
      - [op_cost, bp_y, ">="]
    method: lp
```

```math
\mathit{op\_cost}_{t,g} \ge \mathrm{pwl}_{b \in \mathcal{B}}(\mathrm{x}_{g,b},\ \mathrm{y}_{g,b})(\mathit{dispatch}_{t,g}) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T}
```

Written out by `spec.expand()`:

```math
\mathit{op\_cost}_{t,g} \cdot \left( \mathrm{x}_{g,b} - \mathrm{x}_{g,b \boxminus_{0} 1} \right) \ge \left( \mathrm{y}_{g,b} - \mathrm{y}_{g,b \boxminus_{0} 1} \right) \cdot \left( \mathit{dispatch}_{t,g} - \mathrm{x}_{g,b} \right) + \mathrm{y}_{g,b} \cdot \left( \mathrm{x}_{g,b} - \mathrm{x}_{g,b \boxminus_{0} 1} \right) \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) > 0
```

```math
\mathit{dispatch}_{t,g} \ge \mathrm{x}_{g,b} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) = 0
```

```math
\mathit{dispatch}_{t,g} \le \mathrm{x}_{g,b} \qquad \forall\, g \in \mathcal{G},\ t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) = \lvert \mathcal{B} \rvert - 1
```

```math
\mathrm{x}_{g,b} \text{ is defined} \wedge \mathrm{y}_{g,b} \text{ is defined} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B}
```

```math
\mathrm{x}_{g,b \boxminus_{0} 1} < \mathrm{x}_{g,b} \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) > 0
```

```math
\left( \mathrm{y}_{g,b} - \mathrm{y}_{g,b \boxminus_{0} 1} \right) \cdot \left( \mathrm{x}_{g,b \boxplus_{0} 1} - \mathrm{x}_{g,b} \right) \le \left( \mathrm{y}_{g,b \boxplus_{0} 1} - \mathrm{y}_{g,b} \right) \cdot \left( \mathrm{x}_{g,b} - \mathrm{x}_{g,b \boxminus_{0} 1} \right) \qquad \forall\, g \in \mathcal{G},\ b \in \mathcal{B} \,:\, \mathrm{pos}(b) > 0 \wedge \mathrm{pos}(b) \neq \lvert \mathcal{B} \rvert - 1
```

```math
\lvert \{ b \in \mathcal{B} \,:\, \mathrm{x}_{g,b} \text{ is defined} \} \rvert \ge 2 \qquad \forall\, g \in \mathcal{G}
```

### Special ordered sets

A set prints under Subject to, after the constraints and before the curves, because a solver holds it as a constraint. Under it are the rows it is written out as.

#### Special ordered set of type 2

at most two adjacent members nonzero, one set per snapshot

```yaml
sos:
  adjacent:
    variable: weight
    along: generator
    type: 2
```

```math
\left( \mathit{weight}_{t,g} \right)_{g \in \mathcal{G}} \in \mathrm{SOS}2 \qquad \forall\, t \in \mathcal{T}
```

Written out by `spec.expand()`:

```math
\mathit{adjacent\_seg}_{t,g} \in \{0, 1\} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

```math
\sum_{g \in \mathcal{G}} \mathit{adjacent\_seg}_{t,g} \le 1 \qquad \forall\, t \in \mathcal{T}
```

```math
\mathit{weight}_{t,g} \le \mathit{adjacent\_seg}_{t,g} + \mathit{adjacent\_seg}_{t,g \boxminus_{0} 1} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G}
```

### Assumptions

#### Two parameters compared

two parameters, which is arithmetic like any other

```yaml
assumptions:
  bounds_do_not_cross: "p_min <= p_max"
```

```math
\mathrm{p}^{\mathrm{min}}_{g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G}
```

#### Connective in an assumption

a connective, so the line has no relation to align on

```yaml
assumptions:
  efficiency_is_a_fraction: "eta > 0 AND eta <= 1"
```

```math
\mathrm{eta}_{g} > 0 \wedge \mathrm{eta}_{g} \le 1 \qquad \forall\, g \in \mathcal{G}
```

#### Parameter compared to a literal

one parameter against a literal

```yaml
assumptions:
  lead_times_are_short: "lead <= 3"
```

```math
\mathrm{lead}_{g} \le 3 \qquad \forall\, g \in \mathcal{G}
```

#### Two properties compared

two maps into one set, compared row by row

```yaml
assumptions:
  zones_agree: "bus[zone] == bus[area]"
```

```math
\mathrm{zone}(b) = \mathrm{area}(b) \qquad \forall\, b \in \mathcal{B}
```

#### Reduction in an assumption

a reduction on a side, leaving nothing to quantify

```yaml
assumptions:
  budget_covers_the_peak: "sum(p_max, over=generator) >= budget"
```

```math
\sum_{g \in \mathcal{G}} \mathrm{p}^{\mathrm{max}}_{g} \ge \mathrm{budget}
```

#### Shift in an assumption

a translation inside arithmetic, and a position keeping the vacated row out

```yaml
assumptions:
  ramps_are_gentle:
    holds: "load - shift(load, along=snapshot, offset=1, edge=0) <= budget"
    where: "position(snapshot) > 0"
```

```math
\mathrm{load}_{t,b} - \mathrm{load}_{t \boxminus_{0} 1,b} \le \mathrm{budget} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \mathrm{pos}(t) > 0
```

#### Assumption with a boolean condition

a bare bool parameter as the where

```yaml
assumptions:
  flexible_units_have_headroom:
    holds: "p_min < p_max"
    where: "is_flexible"
```

```math
\mathrm{p}^{\mathrm{min}}_{g} < \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{is\_flexible}_{g}
```

#### Assumption with a property condition

a property comparison as the where, over a frame two dims wide

```yaml
assumptions:
  northern_demand_is_real:
    holds: "load >= 0"
    where: "bus[zone] == 'north'"
```

```math
\mathrm{load}_{t,b} \ge 0 \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \mathrm{zone}(b) = \text{'}\mathrm{north}\text{'}
```

### Where conditions

#### Parameter as a condition

a parameter over nothing, and a mask that is a bare parameter

```yaml
constraints:
  scalar:
    dims: [generator]
    where: "cost"
    expression: units <= budget
```

```math
\mathit{units}_{g} \le \mathrm{budget} \qquad \forall\, g \in \mathcal{G} \,:\, \mathrm{cost}_{g} \text{ is defined}
```

#### Variable and label conditions

a mask on a variable's existence, and one on a dimension's label

```yaml
constraints:
  running:
    dims: [snapshot, bus]
    where: "theta AND snapshot >= 3"
    expression: theta <= load
```

```math
\theta_{b} \le \mathrm{load}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \theta_{b} \text{ exists} \wedge t \ge 3
```

#### Position in a dimension

a position in a dimension, and the same position within a group

```yaml
constraints:
  first:
    dims: [snapshot, generator]
    where: "position(snapshot) == 0 OR position(snapshot, within=snapshot[season]) == 0"
    expression: on == 1
```

```math
\mathit{on}_{t,g} = 1 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{pos}(t) = 0 \vee \mathrm{pos}_{\mathrm{season}(t)}(t) = 0
```

#### Position counted from the end

the same two counted from the end, which print against a size rather than as themselves

```yaml
constraints:
  last:
    dims: [snapshot, generator]
    where: "position(snapshot) == -1 OR position(snapshot, within=snapshot[season]) == -1"
    expression: on == 0
```

```math
\mathit{on}_{t,g} = 0 \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{pos}(t) = \lvert \mathcal{T} \rvert - 1 \vee \mathrm{pos}_{\mathrm{season}(t)}(t) = \lvert \mathcal{T}_{\mathrm{season}(t)} \rvert - 1
```

#### Relation compared to a label

a property compared to a label, to another property, and to nothing

```yaml
constraints:
  northern:
    dims: [snapshot, bus]
    where: "bus[zone] == 'north' AND bus[zone] != bus[area] AND bus[zone]"
    expression: slack <= load
```

```math
\mathit{slack}_{t} \le \mathrm{load}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \mathrm{zone}(b) = \text{'}\mathrm{north}\text{'} \wedge \mathrm{zone}(b) \neq \mathrm{area}(b) \wedge \mathrm{zone}(b) \text{ is defined}
```

#### Constant true condition

a mask that is only the constant true, which the language says is no mask at all — so none prints

```yaml
constraints:
  always:
    dims: [snapshot]
    where: "true"
    expression: spill >= 0
```

```math
\mathit{spill}_{t} \ge 0 \qquad \forall\, t \in \mathcal{T}
```

#### Constant true inside a condition

the same constant *inside* a mask, where it is what the file says and prints

```yaml
constraints:
  redundant:
    dims: [snapshot]
    where: "True AND spill"
    expression: spill >= 0
```

```math
\mathit{spill}_{t} \ge 0 \qquad \forall\, t \in \mathcal{T} \,:\, \mathit{spill}_{t} \text{ exists}
```

#### Constant false condition

the other constant mask, which says the rows are none and is worth seeing

```yaml
constraints:
  never:
    dims: [snapshot]
    where: "false"
    expression: slack >= 0
```

```math
\mathit{slack}_{t} \ge 0 \qquad \forall\, t \in \mathcal{T} \,:\, \bot
```

#### Comparison of two expressions

a mask comparing two expressions, which prints as the arithmetic it is

```yaml
constraints:
  margin:
    dims: [snapshot, generator]
    where: "p_max - p_min > cost / 2"
    expression: p <= p_max
```

```math
p_{t,g} \le \mathrm{p}^{\mathrm{max}}_{g} \qquad \forall\, t \in \mathcal{T},\ g \in \mathcal{G} \,:\, \mathrm{p}^{\mathrm{max}}_{g} - \mathrm{p}^{\mathrm{min}}_{g} > \frac{\mathrm{cost}_{g}}{2}
```

#### Shift and lookup in a condition

a translation under a comparison names its edge, a lookup reads through a property, and the position keeps the vacated row out

```yaml
constraints:
  ramped:
    dims: [snapshot, bus]
    where: "load - shift(load, along=snapshot, offset=1, edge=0) <= at(zone_cap, by=bus[zone]) AND position(snapshot) > 0"
    expression: slack <= load
```

```math
\mathit{slack}_{t} \le \mathrm{load}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \mathrm{load}_{t,b} - \mathrm{load}_{t \boxminus_{0} 1,b} \le \mathrm{zone\_cap}_{\mathrm{zone}(b)} \wedge \mathrm{pos}(t) > 0
```

#### Reduction in a scalar condition

a reduction on a side of a scalar mask, so nothing is left to quantify

```yaml
constraints:
  covered:
    dims: []
    where: "sum(p_max, over=generator) >= budget"
    expression: sum(p) <= budget
```

```math
\sum_{t \in \mathcal{T},\ g \in \mathcal{G}} p_{t,g} \le \mathrm{budget} \qquad \text{where } \sum_{g \in \mathcal{G}} \mathrm{p}^{\mathrm{max}}_{g} \ge \mathrm{budget}
```

#### Count over a dimension

a count of the coordinates a condition admits, which reduces one dim away

```yaml
constraints:
  counted:
    dims: [bus]
    where: "count(tech_cap > 0, over=technology) >= 2"
    expression: theta <= budget
```

```math
\theta_{b} \le \mathrm{budget} \qquad \forall\, b \in \mathcal{B} \,:\, \lvert \{ e \in \mathcal{E} \,:\, \mathrm{tech\_cap}_{b,e} > 0 \} \rvert \ge 2
```

#### Count along a dimension of the frame

the same count along a dim the frame carries, so the set takes a primed dummy

```yaml
constraints:
  counted_here:
    dims: [bus, technology]
    where: "count(tech_cap > 0, over=technology) >= 2"
    expression: theta <= tech_cap
```

```math
\theta_{b} \le \mathrm{tech\_cap}_{b,e} \qquad \forall\, b \in \mathcal{B},\ e \in \mathcal{E} \,:\, \lvert \{ e' \in \mathcal{E} \,:\, \mathrm{tech\_cap}_{b,e'} > 0 \} \rvert \ge 2
```

#### Condition at the previous coordinate

a condition read one coordinate back, which is false where the translation vacates

```yaml
constraints:
  run_start:
    dims: [snapshot, bus]
    where: "load AND NOT shift(load, along=snapshot, offset=1)"
    expression: slack <= load
```

```math
\mathit{slack}_{t} \le \mathrm{load}_{t,b} \qquad \forall\, t \in \mathcal{T},\ b \in \mathcal{B} \,:\, \mathrm{load}_{t,b} \text{ is defined} \wedge \neg \left( \mathrm{load}_{t - 1,b} \text{ is defined} \right)
```

#### Condition through a property

a condition read through a property: a bus is held only where its zone has a cap at all

```yaml
constraints:
  zoned:
    dims: [bus]
    where: "at(zone_cap, by=bus[zone])"
    expression: theta <= budget
```

```math
\theta_{b} \le \mathrm{budget} \qquad \forall\, b \in \mathcal{B} \,:\, \mathrm{zone\_cap}_{\mathrm{zone}(b)} \text{ is defined}
```
<!-- notation:end -->

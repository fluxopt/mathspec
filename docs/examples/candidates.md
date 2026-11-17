<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# A multi-dim as a test and a subset

Two uses of a [multi-dim](../reference/language/relations.md#multi-dims) that
`dims:` cannot state:

- `port_cost` is over every port, and its case `new` tests `candidate`. The
  entry covers both branches, so `candidate` cannot stand in its `dims:`.
- `extendable` is over the one member `unit`, so it lists some units.
  `build`, `unit_limit` and `build_limit` are over `[extendable, period]`, so
  they have coordinates only for the units it lists.

<!-- gallery:begin -->
```yaml
description: >-
  Units whose candidate ports cost more to run, and the units that may be
  extended: a multi-dim as a condition, and a multi-dim over one member.

dimensions:
  unit: { description: a converter }
  port: { description: an output of a unit }
  period: { dtype: int, ordered: true, description: a step of the horizon }
  candidate: { over: [unit, port], description: the ports a unit may add }
  extendable: { over: [unit], description: the units whose capacity may grow }

parameters:
  run_cost: { dims: [unit, port, period], description: the cost of a unit of flow through a port that exists }
  new_cost: { dims: [unit, port, period], description: the cost of a unit of flow through a candidate port }
  capacity: { dims: [unit], description: the most a unit produces in a period }
  max_build: { dims: [extendable], description: the most a unit's capacity may grow }
  load: { dims: [period], description: demand to be met }

variables:
  flow: { dims: [unit, port, period], bounds: { lower: 0 }, description: what a port delivers }
  build: { dims: [extendable, period], bounds: { lower: 0 }, description: the capacity added to a unit }

expressions:
  port_cost:
    description: a candidate port costs its own price, every other port the running price
    dims: [unit, port, period]
    cases:
      new: { when: candidate, expression: new_cost * flow }
    otherwise: run_cost * flow

constraints:
  unit_limit:
    description: the ports of a unit deliver no more than its capacity and what it adds
    dims: [extendable, period]
    expression: sum(flow, over=port) <= capacity + build
  build_limit:
    description: a unit adds no more than its limit
    dims: [extendable, period]
    expression: build <= max_build
  balance:
    description: the ports meet the load
    dims: [period]
    expression: sum(flow, over=[unit, port]) >= load

objective:
  sense: minimize
  expression: sum(port_cost) + sum(build)
```

Units whose candidate ports cost more to run, and the units that may be extended: a multi-dim as a condition, and a multi-dim over one member.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{P}`$ | index $`p`$ — `period` — a step of the horizon |
| $`\mathcal{O}`$ | index $`o`$ — `port` with $`\mathrm{candidate} \subseteq \mathcal{O} \times \mathcal{U}`$, `candidate` is `absent` where the data has no row — an output of a unit |
| $`\mathcal{U}`$ | index $`u`$ — `unit` with $`\mathrm{candidate} \subseteq \mathcal{O} \times \mathcal{U},\ \mathrm{extendable} \subseteq \mathcal{U}`$, `candidate` is `absent` where the data has no row, `extendable` is `absent` where the data has no row — a converter |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{U}`$ — the most a unit produces in a period |
| $`\mathrm{load}`$ | `load` over $`\mathcal{P}`$ — demand to be met |
| $`\mathrm{max\_build}`$ | `max_build` over $`u \in \mathrm{extendable}`$ — the most a unit's capacity may grow |
| $`\mathrm{new\_cost}`$ | `new_cost` over $`\mathcal{P} \times \mathcal{O} \times \mathcal{U}`$ — the cost of a unit of flow through a candidate port |
| $`\mathrm{run\_cost}`$ | `run_cost` over $`\mathcal{P} \times \mathcal{O} \times \mathcal{U}`$ — the cost of a unit of flow through a port that exists |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{build}`$ | `build` over $`u \in \mathrm{extendable},\ p \in \mathcal{P}`$ — the capacity added to a unit |
| $`\mathit{flow}`$ | `flow` over $`\mathcal{P} \times \mathcal{O} \times \mathcal{U}`$ — what a port delivers |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{port\_cost}`$ | `port_cost` over $`\mathcal{P} \times \mathcal{O} \times \mathcal{U}`$ — a candidate port costs its own price, every other port the running price |

#### Variable domains

**`build`**

```math
\mathit{build}_{p,u} \ge 0 \qquad \forall\, u \in \mathrm{extendable},\ p \in \mathcal{P}
```

**`flow`**

```math
\mathit{flow}_{p,o,u} \ge 0 \qquad \forall\, p \in \mathcal{P},\ o \in \mathcal{O},\ u \in \mathcal{U}
```

#### Definitions

**`port_cost`**

```math
\mathit{port\_cost}_{p,o,u} = \begin{cases} \mathrm{new\_cost}_{p,o,u} \cdot \mathit{flow}_{p,o,u} & \text{if } \left( o,\ u \right) \in \mathrm{candidate} \\ \mathrm{run\_cost}_{p,o,u} \cdot \mathit{flow}_{p,o,u} & \text{otherwise} \end{cases} \qquad \forall\, p \in \mathcal{P},\ o \in \mathcal{O},\ u \in \mathcal{U}
```

#### Objective

```math
\min \sum_{p \in \mathcal{P},\ o \in \mathcal{O},\ u \in \mathcal{U}} \mathit{port\_cost}_{p,o,u} + \sum_{p \in \mathcal{P},\ u \in \mathcal{U}} \mathit{build}_{p,u}
```

#### Subject to

**`balance`**

```math
\sum_{o \in \mathcal{O},\ u \in \mathcal{U}} \mathit{flow}_{p,o,u} \ge \mathrm{load}_{p} \qquad \forall\, p \in \mathcal{P}
```

**`build_limit`**

```math
\mathit{build}_{p,u} \le \mathrm{max\_build}_{u} \qquad \forall\, p \in \mathcal{P},\ u \in \mathcal{U} \,:\, u \in \mathrm{extendable}
```

**`unit_limit`**

```math
\sum_{o \in \mathcal{O}} \mathit{flow}_{p,o,u} \le \mathrm{capacity}_{u} + \mathit{build}_{p,u} \qquad \forall\, p \in \mathcal{P},\ u \in \mathcal{U} \,:\, u \in \mathrm{extendable}
```
<!-- gallery:end -->

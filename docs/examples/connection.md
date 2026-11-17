<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Units with ports

Units with ports is a specification of an optimisation model
([a spec](../reference/glossary.md#spec)) in which each unit attaches to buses
through numbered ports. Each port number matches one of the `bus0`, `bus1`, …
columns of an open-source power system modelling framework
([PyPSA](https://pypsa.org)). The dimension `connection` lists the pairs of a
unit and a port, its [members](../reference/language/dimensions.md#over), and
its maps give the bus and the role of each pair. Its label is the pair, not
the bus, so two ports of one unit may attach to the same bus.

`efficiency` is declared over every connection and snapshot. Its
[`where:`](../reference/language/parameters-variables-constraints.md#where)
keeps only the output ports, and `missing: 1` applies only there. At an input
port, `injection` takes its case, and elsewhere `efficiency` times the flow of
the unit, read with `at`. The sum in `balance` adds each connection to the bus
it attaches to.

<!-- gallery:begin -->
```yaml
description: Units that draw power from one bus and deliver it to others, through numbered ports.

dimensions:
  snapshot: { dtype: int, description: dispatch periods }
  bus: { description: nodes of the network }
  unit: { description: "converters, such as an electrolyser or a heat pump" }
  port: { dtype: int, description: "an attachment of a unit, numbered as PyPSA's bus0, bus1, ..." }
  role: { description: input or output }
  connection:
    description: the bus each port of a unit attaches to, and whether the port draws or delivers
    over: [unit, port]

maps:
  connection: { bus: { dim: bus }, role: { dim: role } }

parameters:
  capacity: { dims: [unit], description: the most a unit can draw at its input }
  efficiency:
    description: share of the drawn power that an output port delivers
    dims: [connection, snapshot]
    where: "connection[role] == 'output'"
    missing: 1
  load: { dims: [bus, snapshot], description: demand to be met }
  cost: { dims: [bus], description: price of power bought at a bus }

variables:
  flow:
    description: power a unit draws at its input
    dims: [unit, snapshot]
    bounds: { lower: 0, upper: capacity }
  supply:
    description: power bought at a bus
    dims: [bus, snapshot]
    bounds: { lower: 0 }

expressions:
  injection:
    description: what a port puts into its bus
    dims: [connection, snapshot]
    cases:
      draws: { when: "connection[role] == 'input'", expression: "-at(flow, by=connection[unit])" }
    otherwise: efficiency * at(flow, by=connection[unit])

constraints:
  balance:
    dims: [bus, snapshot]
    expression: supply + sum(injection, over=connection, by=connection[bus]) == load

objective:
  sense: minimize
  expression: sum(cost * supply)
```

Units that draw power from one bus and deliver it to others, through numbered ports.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{B}`$ | index $`b`$ — `bus` with $`\mathrm{bus}: \mathcal{C} \to \mathcal{B}`$ — nodes of the network |
| $`\mathcal{C}`$ | index $`c`$ — `connection`, $`\mathcal{C} \subseteq \mathcal{P} \times \mathcal{U}`$ with $`\mathrm{bus}: \mathcal{C} \to \mathcal{B},\ \mathrm{role}: \mathcal{C} \to \mathcal{R}`$ — the bus each port of a unit attaches to, and whether the port draws or delivers |
| $`\mathcal{P}`$ | index $`p`$ — `port` — an attachment of a unit, numbered as PyPSA's bus0, bus1, ... |
| $`\mathcal{R}`$ | index $`r`$ — `role` with $`\mathrm{role}: \mathcal{C} \to \mathcal{R}`$ — input or output |
| $`\mathcal{T}`$ | index $`t`$ — `snapshot` — dispatch periods |
| $`\mathcal{U}`$ | index $`u`$ — `unit` — converters, such as an electrolyser or a heat pump |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{capacity}`$ | `capacity` over $`\mathcal{U}`$ — the most a unit can draw at its input |
| $`\mathrm{cost}`$ | `cost` over $`\mathcal{B}`$ — price of power bought at a bus |
| $`\mathrm{efficiency}`$ | `efficiency` over $`\mathcal{C} \times \mathcal{T}`$, only where $`\mathrm{role}(c) = \text{'}\mathrm{output}\text{'}`$, $`1`$ where the data has no row — share of the drawn power that an output port delivers |
| $`\mathrm{load}`$ | `load` over $`\mathcal{B} \times \mathcal{T}`$ — demand to be met |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{flow}`$ | `flow` over $`\mathcal{T} \times \mathcal{U}`$ — power a unit draws at its input |
| $`\mathit{supply}`$ | `supply` over $`\mathcal{B} \times \mathcal{T}`$ — power bought at a bus |

#### Definitions

| Symbol | Meaning |
|---|---|
| $`\mathit{injection}`$ | `injection` over $`\mathcal{C} \times \mathcal{T}`$ — what a port puts into its bus |

#### Variable domains

**`flow`**

```math
0 \le \mathit{flow}_{t,u} \le \mathrm{capacity}_{u} \qquad \forall\, t \in \mathcal{T},\ u \in \mathcal{U}
```

**`supply`**

```math
\mathit{supply}_{b,t} \ge 0 \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```

#### Definitions

**`injection`**

```math
\mathit{injection}_{c,t} = \begin{cases} -\mathit{flow}_{t,\mathrm{unit}(c)} & \text{if } \mathrm{role}(c) = \text{'}\mathrm{input}\text{'} \\ \mathrm{efficiency}_{c,t} \cdot \mathit{flow}_{t,\mathrm{unit}(c)} & \text{otherwise} \end{cases} \qquad \forall\, c \in \mathcal{C},\ t \in \mathcal{T}
```

#### Objective

```math
\min \sum_{b \in \mathcal{B},\ t \in \mathcal{T}} \mathrm{cost}_{b} \cdot \mathit{supply}_{b,t}
```

#### Subject to

**`balance`**

```math
\mathit{supply}_{b,t} + \sum_{c \in \mathcal{C} \,:\, \mathrm{bus}(c) = b} \mathit{injection}_{c,t} = \mathrm{load}_{b,t} \qquad \forall\, b \in \mathcal{B},\ t \in \mathcal{T}
```
<!-- gallery:end -->

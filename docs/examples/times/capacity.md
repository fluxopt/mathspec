<!--
SPDX-FileCopyrightText: mathspec contributors
SPDX-License-Identifier: CC-BY-4.0
-->

# Capacity transfer and capacity–activity

This spec ports two TIMES equations for a process without vintages and
without storage, with the upper bound only.

- `eq_cpt` (TIMES `EQ_CPT`, `eqcpt.mod:18-27`) sets the installed capacity
  `cap` of each period from the new capacity of each vintage. `coef_cpt` is
  the share of a vintage that still exists in that period.
- `eq_capact_up` (TIMES `EQ_CAPACT`, `eqcapact.mod:23-50`, the form without
  vintages) limits the activity in each timeslice, summed over the
  timeslices at or below it, to the available capacity.

The GAMS conditions map to the spec as follows:

- `RTP_VINTYR` and `PRC_TS` are dimensions with
  [members](../../reference/language/dimensions.md#over). `act` is over every
  member of both, and `where: "prc_ts AND rtp_vintyr"` keeps the coordinates
  that both list.
- `TS_MAP(R,S,TS)` is the dimension `ts_map`. Its upper timeslice is the
  alias `upper_timeslice`, so the two timeslices are two members.
  `eq_capact_up` reads the activity at each tuple of `ts_map`, sums it to each
  upper timeslice, and reads that back onto `timeslice`.
- `COEF_AF(…,'UP')` is the `where:` of `eq_capact_up`.
- `NCAP_PASTI$PASTYEAR(V)` reads `0` where the data has no row.

The `LO` and `FX` senses of `EQ_CAPACT` are two more constraints of the same
shape. The objective stands in for `EQ_OBJ`, whose coefficients come from the
discounting loops in `eqobjinv.mod`.

<!-- gallery:begin -->
```yaml
description: >-
  Capacity transfer and capacity–activity from TIMES: EQ_CPT and the upper
  form of EQ_CAPACT, for a process without vintages and without storage.

dimensions:
  region: { description: a region of the model }
  period: { dtype: int, ordered: true, description: a milestone year }
  vintage: { dtype: int, description: the period a capacity was built in }
  process: { description: a technology }
  timeslice: { description: "a slice of the year, at any level of the timeslice tree" }
  upper_timeslice: { alias: timeslice, description: a timeslice that another is at or below }
  rtp_vintyr:
    description: the vintages of a process that exist in a period (RTP_VINTYR)
    over: [region, vintage, period, process]
  prc_ts:
    description: the timeslices a process operates at (PRC_TS)
    over: [region, process, timeslice]
  ts_map:
    description: each timeslice and the timeslices at or below it (TS_MAP)
    over: [region, upper_timeslice, timeslice]

parameters:
  coef_cpt: { dims: [region, vintage, period, process], description: the share of a vintage that still exists in a period }
  ncap_pasti: { dims: [region, vintage, process], missing: 0, description: capacity built before the first period }
  coef_af_up: { dims: [region, period, process, timeslice], missing: absent, description: the upper availability factor }
  prc_capact: { dims: [region, process], description: the activity a unit of capacity can produce in a year }
  g_yrfr: { dims: [region, timeslice], description: the share of the year a timeslice covers }
  obj_icost: { dims: [region, vintage, process], description: "the cost of a unit of new capacity, discounted" }
  obj_acost: { dims: [region, period, process], description: "the cost of a unit of activity, discounted" }

variables:
  ncap: { dims: [region, vintage, process], bounds: { lower: 0 }, description: new capacity (VAR_NCAP) }
  cap: { dims: [region, period, process], bounds: { lower: 0 }, description: installed capacity (VAR_CAP) }
  act:
    description: activity of a vintage of a process in a timeslice (VAR_ACT)
    dims: [region, vintage, period, process, timeslice]
    where: "prc_ts AND rtp_vintyr"
    bounds: { lower: 0 }

constraints:
  eq_cpt:
    description: the installed capacity of each period, from the new capacity of each vintage (EQ_CPT)
    dims: [region, period, process]
    expression: cap == sum(coef_cpt * (ncap + ncap_pasti), over=vintage)
  eq_capact_up:
    description: activity summed over the timeslices at or below each one, up to the available capacity (EQ_CAPACT, UP)
    dims: [region, period, process, timeslice]
    where: coef_af_up
    expression: >-
      sum(sum(at(sum(act, over=vintage), by=ts_map[region, timeslice]), over=ts_map, by=ts_map[region, upper_timeslice]),
        over=upper_timeslice, by=upper_timeslice[timeslice])
      <= coef_af_up * prc_capact * g_yrfr * cap

objective:
  sense: minimize
  expression: >-
    sum(obj_icost * ncap)
    + sum(obj_acost * sum(act, over=[vintage, timeslice]))
```

Capacity transfer and capacity–activity from TIMES: EQ\_CPT and the upper form of EQ\_CAPACT, for a process without vintages and without storage.

#### Sets

| Symbol | Meaning |
|---|---|
| $`\mathcal{T}`$ | index $`t`$ — `period` — a milestone year |
| $`\mathcal{Q}`$ | index $`q`$ — `prc_ts`, $`\mathcal{Q} \subseteq \mathcal{P} \times \mathcal{R} \times \mathcal{S}`$ — the timeslices a process operates at (PRC\_TS) |
| $`\mathcal{P}`$ | index $`p`$ — `process` — a technology |
| $`\mathcal{R}`$ | index $`r`$ — `region` — a region of the model |
| $`\mathcal{K}`$ | index $`k`$ — `rtp_vintyr`, $`\mathcal{K} \subseteq \mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{V}`$ — the vintages of a process that exist in a period (RTP\_VINTYR) |
| $`\mathcal{S}`$ | index $`s`$ — `timeslice` — a slice of the year, at any level of the timeslice tree |
| $`\mathcal{M}`$ | index $`m`$ — `ts_map`, $`\mathcal{M} \subseteq \mathcal{R} \times \mathcal{S} \times \mathcal{S}`$ — each timeslice and the timeslices at or below it (TS\_MAP) |
| $`\mathcal{S}`$ | index $`s'`$ — `upper_timeslice`, an alias of `timeslice` — a timeslice that another is at or below |
| $`\mathcal{V}`$ | index $`v`$ — `vintage` — the period a capacity was built in |

#### Parameters

| Symbol | Meaning |
|---|---|
| $`\mathrm{coef\_af\_up}`$ | `coef_af_up` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{S}`$, `absent` where the data has no row — the upper availability factor |
| $`\mathrm{coef\_cpt}`$ | `coef_cpt` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{V}`$ — the share of a vintage that still exists in a period |
| $`\mathrm{g}^{\mathrm{yrfr}}`$ | `g_yrfr` over $`\mathcal{R} \times \mathcal{S}`$ — the share of the year a timeslice covers |
| $`\mathrm{ncap}^{\mathrm{pasti}}`$ | `ncap_pasti` over $`\mathcal{P} \times \mathcal{R} \times \mathcal{V}`$, $`0`$ where the data has no row — capacity built before the first period |
| $`\mathrm{obj\_acost}`$ | `obj_acost` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R}`$ — the cost of a unit of activity, discounted |
| $`\mathrm{obj\_icost}`$ | `obj_icost` over $`\mathcal{P} \times \mathcal{R} \times \mathcal{V}`$ — the cost of a unit of new capacity, discounted |
| $`\mathrm{prc\_capact}`$ | `prc_capact` over $`\mathcal{P} \times \mathcal{R}`$ — the activity a unit of capacity can produce in a year |

#### Variables

| Symbol | Meaning |
|---|---|
| $`\mathit{act}`$ | `act` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R} \times \mathcal{S} \times \mathcal{V}`$ — activity of a vintage of a process in a timeslice (VAR\_ACT) |
| $`\mathit{cap}`$ | `cap` over $`\mathcal{T} \times \mathcal{P} \times \mathcal{R}`$ — installed capacity (VAR\_CAP) |
| $`\mathit{ncap}`$ | `ncap` over $`\mathcal{P} \times \mathcal{R} \times \mathcal{V}`$ — new capacity (VAR\_NCAP) |

#### Variable domains

**`act`**

```math
\mathit{act}_{t,p,r,s,v} \ge 0 \qquad \forall\, t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R},\ s \in \mathcal{S},\ v \in \mathcal{V} \,:\, \left( p,\ r,\ s \right) \in \mathrm{prc\_ts} \wedge \left( t,\ p,\ r,\ v \right) \in \mathrm{rtp\_vintyr}
```

**`cap`**

```math
\mathit{cap}_{t,p,r} \ge 0 \qquad \forall\, t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R}
```

**`ncap`**

```math
\mathit{ncap}_{p,r,v} \ge 0 \qquad \forall\, p \in \mathcal{P},\ r \in \mathcal{R},\ v \in \mathcal{V}
```

#### Objective

```math
\min \sum_{p \in \mathcal{P},\ r \in \mathcal{R},\ v \in \mathcal{V}} \mathrm{obj\_icost}_{p,r,v} \cdot \mathit{ncap}_{p,r,v} + \sum_{t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R}} \mathrm{obj\_acost}_{t,p,r} \cdot \left( \sum_{s \in \mathcal{S},\ v \in \mathcal{V}} \mathit{act}_{t,p,r,s,v} \right)
```

#### Subject to

**`eq_capact_up`**

```math
\sum_{s' \in \mathcal{S} \,:\, s' = s} \sum_{m \in \mathcal{M} \,:\, \mathrm{region}(m) = r \wedge \mathrm{upper\_timeslice}(m) = s'} \sum_{v \in \mathcal{V}} \mathit{act}_{t,p,\mathrm{region}(m),\mathrm{timeslice}(m),v} \le \mathrm{coef\_af\_up}_{t,p,r,s} \cdot \mathrm{prc\_capact}_{p,r} \cdot \mathrm{g}^{\mathrm{yrfr}}_{r,s} \cdot \mathit{cap}_{t,p,r} \qquad \forall\, t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R},\ s \in \mathcal{S} \,:\, \mathrm{coef\_af\_up}_{t,p,r,s} \text{ is defined}
```

**`eq_cpt`**

```math
\mathit{cap}_{t,p,r} = \sum_{v \in \mathcal{V}} \mathrm{coef\_cpt}_{t,p,r,v} \cdot \left( \mathit{ncap}_{p,r,v} + \mathrm{ncap}^{\mathrm{pasti}}_{p,r,v} \right) \qquad \forall\, t \in \mathcal{T},\ p \in \mathcal{P},\ r \in \mathcal{R}
```
<!-- gallery:end -->

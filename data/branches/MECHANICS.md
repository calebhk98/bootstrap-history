# Node `mechanics`

The engine never names a technology id (CLAUDE.md 4.7). Behaviour that belongs
to a particular technology is declared on the node, in a `mechanics` object:

    "mechanics": {"<mechanic name>": <parameters>, ...}

The engine asks "which nodes declare this mechanic" (`MechanicsMixin` in
`sim/engine/mechanics.py`), so a mod that adds a node, or overrides one with
`"override": true` (a deep merge, `null` deletes a key), gets or loses the
behaviour by declaring or dropping the mechanic. Nothing else needs editing.

Numbers under `mechanics` are `temporary_heuristic` values in the sense of
CLAUDE.md 4.4 unless the spec carries a `source`. This file gives no figures because they
change; read them from the node data (no command summarises them).

## Shared parameter names

* `flat`, `per_unit`, `per_sqrt_unit`: the size of an additive effect. `per_unit`
  and `per_sqrt_unit` scale with how much of a scalable institution runs
  (`institution_units`); `flat` does not.
* `factor`: a multiplicative effect. `factor_per_unit_power`: the multiplier is
  one plus this times units raised to the engine's hiring exponent.
* `gate`: `"has"` if merely knowing the node counts; the default is that the
  node must be operating (`running`).
* `group`: within a channel, only the first holder of a group counts.
* `order`: sequence in which an effect channel is applied. It is stored only
  where floating-point results depend on it.
* `book_money`: the amount is in book money and is scaled to the civilisation's
  coin.
* `tier`: for chains where only the best holder counts (`effect_best`).

## Effect channels (engine reads every holder of the channel)

| Mechanic | Meaning |
|---|---|
| `standing` | reputation floor added while held (`flat`, `per_sqrt_unit`) |
| `credit_line`, `debt_rate_discount`, `living_cost_status` | credit limit, interest discount, status upkeep |
| `patron_protection`, `protection` | protection added; the first is weighted by the society's patronage weight |
| `alarm_factor`, `eminence_hazard_factor` | multipliers on alarm and on prominence hazard; the latter may carry `hint_when_running` / `hint_when_absent` advice text |
| `confiscation_dispersal`, `market_standing`, `mine_ceiling` | best holder by `tier` wins |
| `reach` | multiplier on goods market reach |
| `workshop_markup` | added to the workshop wage markup |
| `supervision_room` | people one can oversee; carries `words` shown in the breakdown |
| `hiring_factor`, `market_hiring_factor` | multipliers on the hiring pool in the two places it is computed |
| `staff_capacity` | scholars, artisans, directors an institution trains; `scales_with_units`, `must_be_running` |
| `room_places` | household places the institution adds (advice and ceiling) |
| `institution_places` | people one unit supports (upkeep scaling) |
| `labour_productivity` | `trade` and `bonus` for that trade's hour |
| `schooling_flow` | schooling contribution; `required` makes it a precondition of all schooling |
| `mining_tech` | `yield` and `cost` multipliers on mining, optionally limited to `materials` |
| `hazard_counters` | list of `{kind, share, label, order}`: what harm the node counters |
| `staff_grant` | people granted once on completion when auto-hire is off |
| `staff_advice` | `kind` (`scholars`/`artisans`), `advice` text shown when staff is short |

## Flags and small specs

| Mechanic | Meaning |
|---|---|
| `capability` | a capability institution: `lost_benefit` text, `scalable` (`"literacy"` or `"population"` sets which ceiling bounds its units), `redundant_with` (ids whose operation makes a closed copy harmless) |
| `disease_burden` | counts toward the society's disease burden (weights live in the civilisation tech effects) |
| `founder_life_extension` | extends the founder's life while operating |
| `corpus` | a knowledge hedge: `rank` (higher is better), `loss_chance`, `fraction_lost`, `diffusion_pace`, `dispersed` |
| `patron`, `patron_lost_to_eminence`, `patron_mortal`, `state_funding`, `state_approval` | patronage roles: `patron.tier`; which patrons can be lost or die; who funds work; which patron lifts the state's `wary` or `opposed` gate |
| `workshop_site`, `hosts_bought_people` | where a workshop's output and bought workers come from |
| `failure_relief` | `failure_kind` of node failures it reduces |
| `supplies_material_by_sea_route` | `materials` it brings by an existing trade route |
| `farming_technique` | `axis` (`rotation`, `toolkit`, `crop`) and `entry` (a name in `sim/world/agriculture.py`) |
| `ablation_candidate` | offered by the `sensitivity` command |
| `power_tier`, `power_generation`, `prime_mover`, `electricity_gate`, `electrical_process` | the power ladder: `rank`, `label`, `anchor_kw`, `scale`; generator `role` and `tier`; prime-mover `family`; nodes whose presence means "needs generated electricity"; process electricity per kg |

Every mechanic name used in the tree must appear in this file
(`sim/tests/test_engine_content_ids.py` checks it).

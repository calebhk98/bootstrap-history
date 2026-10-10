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
* `labour_hours`: the amount is in labour hours and is priced in the civilisation's
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
| `mine_works` | a physical term of the mine's works, read by `sim/world/mine_technique.py`: `drainage_lift_efficiency`, `gravity_drained_head_share`, `gravel_moved_multiple`, `drainage_engine` and `hoist_engine` (`{lift_power_watts, attendants, fuel_kg_per_tonne_metre}`), `blasting` (`{drilling_hours_per_tonne_rock: {soft, medium, hard}, charging_hours_per_tonne_rock}`), `drilling_rate_multiple`, `haulage_load_kilograms`; carries a `source`. Techniques that act on one term compete (the cheapest device or explosive is used) and never stack |
| `hazard_counters` | list of `{kind, share, label, order}`: what harm the node counters. An entry may add `requires_running` (works that must be open), `magazine` (`{material: units}` held in the stock ledger for the counter to count in full; it counts for the share held) and `draws` (`{material: units}` spent from the ledger in each year a threat of its kind is live). The node's own `garrison` (see CONTRACT) is read the same way: the counter counts for the share of the garrison present |
| `banks_output` | `material` and `per_labour_hour`: a running work puts that material into the stock ledger each year from its crew's hours (`sch` plus `art` people); the crew's inputs are bought inside the work's running costs (`sim/engine/defence_stores.py`) |
| `staff_grant` | people granted once on completion when auto-hire is off |
| `staff_advice` | `kind` (`scholars`/`artisans`), `advice` text shown when staff is short |

## Flags and small specs

| Mechanic | Meaning |
|---|---|
| `capability` | a capability institution: `lost_benefit` text, `scalable` (`"literacy"` or `"population"` sets which ceiling bounds its units), `redundant_with` (ids whose operation makes a closed copy harmless) |
| `patent_grant` | a state that knows the node grants term-limited exclusive rights to inventions (`sim/agents/patent.py`); without a node declaring it no patent is ever granted |
| `state_credit` | holding it lets a state borrow against its revenue (`source`); without a holder a deficit cuts spending |
| `disease_burden` | counts toward the society's disease burden (weights live in the civilisation tech effects) |
| `founder_life_extension` | extends the founder's life while operating |
| `corpus` | a knowledge hedge: `rank` (higher is better), `loss_chance`, `fraction_lost`, `diffusion_pace`, `dispersed` |
| `patron`, `patron_lost_to_eminence`, `patron_mortal`, `state_funding`, `state_approval` | patronage roles: `patron.tier`; which patrons can be lost or die; who funds work; which patron lifts the state's `wary` or `opposed` gate |
| `workshop_site`, `hosts_bought_people` | where a workshop's output and bought workers come from |
| `failure_relief` | `failure_kind` of node failures it reduces |
| `precaution` | `kind` (`pilot_plant`, `redundant_team`): paying for it at start adds a share of the bill and of the founder's hours and lowers the failure chance; the figures per kind are declared in `sim/engine/projects_precaution.py`, and a node may override them (`cost_share`, `hours_share`, `relief_per_cost_share`) only with a `source`. Quoted as `pay_to_lower_the_risk` in `why` |
| `diagnosis_instrument` | `instrument` (node id whose holder can measure the work's result), `quantity`, `needed` and `unit` (larger is worse), `needed_words`; without the instrument a failure adds no retry learning and the report says which instrument was missing, with it the report gives the figure reached against `needed` |
| `supplies_material_by_sea_route` | `materials` it brings by an existing trade route |
| `farming_technique` | `axis` (`rotation`, `toolkit`, `crop`) and `entry` (a name in `sim/world/agriculture.py`) |
| `ablation_candidate` | offered by the `sensitivity` command |
| `upkeep_full` | the work bills its whole upkeep every year it is open, whatever the household headcount: for a work that serves a town or a state rather than the household's own people (see Benefactions below) |
| `power_tier`, `power_generation`, `prime_mover`, `electricity_gate`, `electrical_process` | the power ladder: `rank`, `label`, `anchor_kw`, `scale`; generator `role` and `tier`; prime-mover `family`; nodes whose presence means "needs generated electricity"; process electricity per kg |

## Benefactions

Works that a rich person or company pays for with no takings of their own
(`data/branches/56_benefactions.json`, ids starting `ben_`) are ordinary nodes:
`rev` is 0, cost comes from `lab` and `mat`, and `up` is derived from annual
staff hours and consumables plus a share of the build (each node's `_internal`
field gives the working). They act only through the channels above:
`schooling_flow` and `standing` (schools, libraries), `staff_capacity`
(foundations, patronage), `hazard_counters` (hospitals, water, granaries,
harbours, insurance), `protection`, `patron_protection`, `alarm_factor` and
`eminence_hazard_factor` (games, temples, grants to the state), `credit_line`
and `debt_rate_discount` (a house bank), `reach` and `supervision_room`
(harbours, telegraph, expeditions). `capability.scalable` makes each repeatable,
dearer each time. A work's effect holds only while its doors are open, so
stopping the upkeep stops the effect. Every size is a `temporary_heuristic`.

Every mechanic name used in the tree must appear in this file
(`sim/tests/test_engine_content_ids.py` checks it).

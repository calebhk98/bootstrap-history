# Module `campaigns`

Armies, campaigns, conquest, captives and revolts.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 3 / 5 |
| Old methods and properties owned (after regrouping) | 46 |
| Of those, referenced from another module's mixin code | 0 (0 classed read-only or pure by Appendix B, 0 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 8 (0 from mixins, 8 only from outside) |
| Views per used name | 0.38 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 3 |
| Views of other modules it reads | 9, from 5 modules |
| Commands of other modules it sends | 1 |

**Existing surface and files.** Existing: `sim/agents/army_raising.py`, `revolt.py`, `unrest.py`, `ruler.py`, `bonded_sale.py`. Engine: `CampaignActorsMixin` (17), `CampaignYearMixin` (18), `RevoltYearMixin` (8), `CaptivesMixin` (3).

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `CampaignActorsMixin` | `sim/engine/campaign_actors.py` | 17 | 0 |
| `CampaignYearMixin` | `sim/engine/campaign_year.py` | 18 | 0 |
| `RevoltYearMixin` | `sim/engine/revolt_year.py` | 8 | 0 |
| `CaptivesMixin` | `sim/engine/captives.py` | 3 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_add_captives`, `_camp`, `_campaign_army`, `_consolidate_conquests`, `_contest`, `_defend`, `_disputed_accession`, `_draw_down`, `_faction_readings`, `_garrison`, `_garrison_on`, `_keep_within_force`, `_pay_years`, `_reference_equipment`, `_rising`, `_rout`, `_stability_of`, `_state_grievance`, `_take`, `_withdraw`, `acting_owner`, `army_of`, `army_records`, `campaign_column`, `campaign_modes`, `campaign_site`, `campaign_store`, `own_army`, `owner_force`, `owner_government`, `owner_has_state`, `owner_world`, `save_army`, `stability_owners`, `strike_from_force`, `take_captives_from_battle`, `take_captives_from_conquest`, `tile_fortification`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `CampaignsWorld`, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.campaigns` | world | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `armies` | keyed | no | Armies by owner: records, force, free soldiers, the owner's government and world. | `army_of`, `armies_of`, `army_records`, `free_soldiers`, `owner_force`, `owner_government`, `owner_world`, `owner_has_state`, `acting_owner`, `campaign_store` | `economy.campaigns` | `land.tile_owner`, `polity.state_treasury` | `campaigns` | 1 |
| `campaign_sites` | keyed | no | Sites a campaign may reach, fortification, columns and modes. | `campaign_site`, `tile_fortification`, `campaign_modes`, `campaign_column` | - | `land.tile_owner`, `land.transport`, `demography.people_by_tile` | `campaigns` | 0 |
| `stability` | keyed | no | Stability and grievance of each owner; the factions' readings. | `stability_owners`, `_stability_of`, `_state_grievance`, `_faction_readings`, `_garrison_on` | - | `demography.food_eaten`, `armies` | `campaigns` | 0 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `armies`, `campaign_sites`, `stability`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 0 methods are referenced from other modules' mixin code: 0 are replaced by a view here, 0 by a command. 8 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 8 used names, 8 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_garrison_on`, `_stability_of`, `armies_of`, `army_of`, `army_records`, `campaign_column`, `campaign_site`, `campaign_store`, `free_soldiers`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `RaiseArmy` | owner, tile, size | `raise_army`, `own_army`, `save_army`. Methods: `raise_army` | `sim/ui/proto/ (campaign commands)`, `sim/engine/campaign_actors.py` | `no_state`, `too_few_soldiers` | `economy.campaigns` |
| `OrderArmy` | owner, army, order | `order_army`, `recall_army`, `disband_army`, `strike_from_force`. Methods: `order_army`, `recall_army`, `disband_army` | `sim/engine/campaign_actors.py` | `no_such_army` | - |
| `ResolveCampaigns` | year | `step_campaigns` (`_contest`, `_take`, `_rout`, `_consolidate_conquests`): sends TransferTile, KillPeople, MoveGoods. Methods: `step_campaigns` | `sim/engine/campaign_year.py` | none: always applies | - |
| `ResolveRevolts` | year | `step_revolts`. Methods: `step_revolts` | `sim/engine/revolt_year.py` | none: always applies | - |
| `TakeCaptives` | owner, source, count | `take_captives_from_battle`, `take_captives_from_conquest`. | `sim/engine/captives.py` | none: always applies | - |

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.of_kind, actors.state, actors.world_of_country)
- `demography`: `demography.food_eaten` (input of campaigns.stability, population.regional_eaten_over_need); `demography.people_by_tile` (input of campaigns.campaign_sites)
- `land`: `land.tile_facts` (world_map, world_map.tiles); `land.tile_owner` (input of campaigns.armies, input of campaigns.campaign_sites, tile_owner, tile_owner_map); `land.tiles_owned_by` (tiles_owned_by); `land.transport` (economy.improvements, held_and_running, input of campaigns.campaign_sites)
- `polity`: `polity.state_treasury` (input of campaigns.armies)
- `stores`: `stores.store` (stores, stores.view)

Sends (commands of other modules):

- `land`: `TransferTile`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `campaigns`
- `revolts`

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 6 | `raise_army`, `order_army`, `recall_army`, `disband_army`, `armies_of`, `free_soldiers` |
| engine/(function modules) | 2 | `step_campaigns`, `step_revolts` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `raise_army`, `order_army`, `recall_army`, `disband_army`, `armies_of`, `free_soldiers`; engine: `step_campaigns`, `step_revolts`.

## (h) Hard spots and caches

- Reads `tile_owner` 7+4+2+1 times through `TileOwnershipMixin` and writes ownership through `transfer_tile`: the cleanest example of view-in, command-out.
- Campaign resolution iterates armies and tiles in sorted order with random draws; order of commands to land and demography must match the old order.
- Reads a mod store (`stores`) for campaign modes.

Caches and version counters held today (feed for task 1.2):

- `__dict__['_campaign_sites']` (`campaign_year.py:25`)

Detected by the cache scan in this module's mixin files: `engine/campaign_year.py:25 __dict__[_campaign_sites]`.

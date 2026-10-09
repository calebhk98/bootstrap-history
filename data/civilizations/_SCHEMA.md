# Civilization schema

The tech tree says **X requires Y**. It never says "tech level 4", and it never
says "Rome". Everything specific to a place and a century lives here, in one
file per civilization, so that swapping Rome for Han China, Viking Norway,
Mexica Tenochtitlan, Plantagenet England or somewhere invented is a matter of
pointing the simulator at a different file.

That is also why the tree has no linear tech levels. **A civilization can have
aeroplanes and no gunpowder, or electricity and no steam, or steam and no
electricity, or cities built on rafts because the land will not farm.** The only
thing that constrains it is the prerequisite graph.

```
python3 rome/sim/simulator.py run --civ rome_100ad
python3 rome/sim/simulator.py run --civ han_china_100ad
python3 rome/sim/simulator.py civs            # list what is available
```

## Fields

| field | meaning |
|---|---|
| `id`, `name`, `year`, `blurb` | identity |
| `society` | Optional. Which society's institutions are native here, matched against `data/institution_societies.json`; absent means the civilisation's own `id`. A node carrying another society's marker is foreign. |
| `population`, `urban_fraction`, `literacy_elite`, `literacy_general` | demography |
| `standing_army` | Soldiers the state keeps in pay at the start date, an initial condition like `population`; the state holds the same share of its people as the population changes. Its pay, equipment and the staff it draws from the labour pool are the state's budget (`sim/agents/budget.py`). Missing means no standing force. Carries a source and confidence under `_internal`. |
| `currency_words` | `{"long": ..., "short": ...}`: how the money reads in a sentence ("you have 400 ___") and in compact lines. Absent: the `currency` field is used. |
| `currency`, `price_index`, `wage_index` | economy scaling. 1.0 is Rome 100 AD, which is the calibration baseline for `prices.json`. |
| `coin_standard` | **Required.** `{material, kg_per_unit, source}`: what one unit of the civilisation's money stands for physically, e.g. the silver in a denarius; optional `fineness` (share of the coin's mass that is that material, a share above 0 up to 1) and `mint_charge_share` (struck coin only). Money is anchored to it: a labour hour is worth the reciprocal of the coin's solved labour hours. The material must be priceable with the civilisation's starting technologies, or loading fails. |
| `staple` | Optional. The grain material the subsistence basket (the wage floor) is priced in; absent means `wheat_kg`. It must be a good with a production entry the civilisation can make with its starting technologies, and a food effectiveness in `data/world/needs.json` (the subsistence quantity is in kg wheat equivalent, so a richer grain needs fewer kilograms). |
| `starting_interest_rate`, `starting_tax_share` | **Required.** Yearly rate on arrears, and share of a household's revenue taken by tax and dues, at the civilisation's start date. Initial conditions, held constant for now; a missing or non-numeric value is a load error. Each carries a source and confidence under `_internal`. |
| `state_revenue` | List of the forms of revenue the state raises: `form` (name), `basis` (a base the engine models: `harvest`, `adult_labour_years`, `imports_value`, `exports_value`, `coin_stock`; see `sim/agents/revenue_bases.py`), `rate` (share of the base), optional `paid_in` (a material; the share is taken in kind, so the basis must yield that material), and `_internal` with a source and confidence. Absent means the state raises nothing. `starting_tax_share` no longer sets state revenue; it remains the ordinary share on a visible household. |
| `state_capacity` | 0 to 1. Can the state fund and compel a large project? Rome 0.85, Norse 0.15. |
| `starting_techs` | **Required, exhaustive, duplicate-free** node ids the civilization already has, including its material and capability nodes. Every id must exist in the universal graph or scenario loading fails. The engine never infers ownership from tier, cost, or another civilization's prerequisites: a zero-cost/tier-0 node absent from this list remains unknown. A different civ has a different free list. |
| `prerequisite_gaps` | `{node_id: reason}`: held nodes whose own `pre` the civilisation does not hold. `validate` errors on an undeclared gap; the reason `"unreviewed"` only warns. Write a real reason only where the history is clear, with its source. |
| `home_tiles` | **Required for shipped civilisations.** The tiles it holds at the start, listed directly and sorted. Reach, settlement, roads and freight all read the tiles held (`sim.geography.api.tiles_held`). A mod may instead give `home_regions`, region labels that resolve to the tiles carrying them, as a shorthand; when both are present `home_tiles` wins. Shipped files list tiles only, so no second map can drift from the first. |
| `institutions` | which legal vehicles exist: partnership, corporation, guild, testament, charter, bank, patent |
| `values` | the REACTION MODEL. See below. |
| `hazards` | dated shocks: plagues, invasions, dynastic collapse, with year ranges. A `staff_loss` hazard now also costs the whole society population (`Sim.pop_deficit`, core.py), which raises `wage_index` until it recovers - see `_demographic_recovery` in core.py. Keep each civilization's list spread across its whole playable span (roughly every 50-90 years, start to start+700): a list that goes quiet for centuries reads as the game having stopped, not as a peaceful age. An optional `condition` on a hazard (resolved by `SocietyMixin._resolve_hazard_condition` in society.py) says whether ITS OWN NAMED CAUSE still holds given what the player has built: `{"field": "<one of staff_loss/sack_chance/output_factor/real_erosion>", "requires_all": [<tech ids>], "outcome": "avert"\|"alter", "alter_scale": <0-1, alter only>, "met_message": "...", "unmet_message": "..."}`. Only ever add one to a hazard whose `note` names a MATERIAL cause (a supply line, a building material, a drainage engine) that a household's own building plausibly removes - never to a succession, a religious policy or an administrative reform, which fire on schedule regardless of what one household built, exactly as history did. Both messages are mandatory: an averted or altered hazard that says nothing is indistinguishable from one the game forgot to fire. An optional `causes` list on a hazard states the situation the event depended on (resolved by `sim/engine/event_causes.py`): each entry is `{"quantity": <name>, "op": ">"\|">="\|"<"\|"<="\|"==", "value": <number>, "why": "<the historical situation the threshold comes from>"}` with optional `relative_to_start` (read `value` as a share of the start value; only for quantities that have one) and `node` (the technology for `state_holds`). Quantities are listed in `QUANTITIES` in that module; `validate` rejects an unknown one. All causes must hold or the event is skipped that year; `"causes_effect": "scale"` instead weakens it by how far they hold. The `why` is mandatory and never a value tuned so the event fires on time. The `divergence` screen and the `risk` forecast use the same evaluation. |
| `cost_multipliers` | what this society finds harder or easier than Rome, by node category and trait. Above 1 is dearer here. |
| `handicap_remedies` | per `cost_multipliers` key: `{"node": ..., "residual": ...}`. Building that node drops the multiplier to `residual`. |
| `briefing_absent` | `[{"claim": ..., "nodes": [ids]}]`: what the civilisation's briefing says it lacks; `validate` errors if `starting_techs` holds any of the nodes. |
| `needs_first` | HARD gates, as against the soft ones above: `{"<label>": {"node": ..., "because": ..., "ids": [...]}}`. Those ids cannot be STARTED at all until `node` is done, and the refusal quotes `because`. For what is not dear here but impossible - the Mexica had no draught animal of any kind, so a horse collar is not a 1.3x agriculture cost, it is nothing you can build. Always liftable by the node it names. An entry may also carry `material` and `units`: the gate then lifts as soon as that much of the material is held, however it came (see `opening_stock`). |
| `opening_stock` | `{material: units}`: living stock (silkworm eggs, a founding herd, planting stock) the civilisation holds at its date, credited to the held-stock ledger at the start. A node whose `holds` names the material opens only while it is held. Initial conditions only. |
| `will_not_sell` | `[material]`: goods this civilisation, as a trade partner, will not sell abroad (eggs of a monopoly crop). The foreign trade and a purchase from it both respect it. A transitional field: an actor-based export policy (`sim/agents/policy.py`) would replace it. |
| `state_pressure` | How THIS state leans on a household once it is large enough to be worth leaning on - read by `SocietyMixin.requisition_report`/`office_report`/`military_demand_eligible`/`confiscation_risk`/`state_pressure_report` (society.py), gated everywhere on `state_notice()` (`state_capacity` times how large and visible the household already looks - see that method's own docstring). `requisition_name`/`office_name`/`military_name`/`confiscation_name` are the words a log line or `risk` uses for this civilisation's version of each; the matching `*_note` is the historical grounding; How much of a year's revenue the state takes is not set here: it follows the state's unfunded need (`sim/agents/budget.py`). Requisition is bargained down by `protection`; office is not - it is compulsory, and gives protection back instead, see `update_protection`. Each civilisation has its own words for each: Rome's annona and munera, Han's salt and iron monopolies and corvee, English purveyance, what is owed at the Norse thing, Mexica tribute. |
| `notes` | what a newcomer must know |
| `debt_bondage`, `bondage_years` | Optional. Whether debt servitude is a recognised institution and how long a term runs. Either one makes the default strata split (`sim/agents/strata_seed.py`) add a bonded stratum; without them the default split has none. |
| `cast` | Optional. The roster this civilisation adds to a game, read by `sim/agents/cast.py` (the roster is seeded once and saved; see `sim/agents/MULTIPLAYER.md`). An object with any of: `strata` (list of the bodies of people the country starts with, each with `name` and `share` of the population, and optionally `trade`, `literacy`, `property_share`, `own_plot`, `work_share`, `bonded` with its `owner` stratum, and `rises_to` and `falls_to` naming the strata its members move to; see `sim/agents/strata_seed.py` for the default split; when absent the strata are derived from `population`, `urban_fraction`, the literacy fields and the bondage fields), `treasury` (the government's opening money, booked as coming from `edge:opening`), `location` (a place id; defaults to the first `home_regions` entry), `countries` (list of civilisation-like dicts for countries that have no file of their own), `actors` (list of cast entries, for example a second player: `actor_id` is required, then `kind`, `name`, `controller`, `policy_kind`, `money`, `location`, `country`; any other field is passed to the actor as a parameter). Keys under `cast` that nothing reads are kept on the country profile. Mods patch the key like any other civilisation field. Foreign countries also come from the economies enabled for the start year in `data/world/foreign_economies.json`. |

## The values vector, and why it replaces `gov` and `sus`

The old model gave each technology a single number for "the State likes it" and
a single number for "this looks like sorcery". Both are properties of the
SOCIETY, not of the technology. A printing press is subversive in a society that
controls information through a scribal elite and unremarkable in one that does
not. Gunpowder is a gift to a centralised empire and a threat to a fragmented
one.

So a technology now carries **traits**, and a civilization carries **weights**,
and the reaction is the dot product.

| trait on a technology | meaning |
|---|---|
| `military` | improves war-making |
| `labour_saving` | displaces workers |
| `information` | moves, copies or stores knowledge |
| `spectacle` | visibly astonishing |
| `inexplicable` | produces an effect with no visible cause |
| `medical` | heals |
| `food` | feeds |
| `infrastructure` | roads, water, harbours, power |
| `luxury` | status goods for the rich |
| `commerce` | trade, finance, records |
| `religious_adjacent` | touches burial, the body, the heavens, or omens |
| `weapon_democratising` | arms individuals rather than states |
| `status_threatening` | undermines an existing elite's monopoly |

| weight on a civilization | meaning |
|---|---|
| `w_military` | how much the state rewards military value |
| `w_labour_saving` | NEGATIVE where cheap coerced labour makes machines unwelcome |
| `w_information` | negative where an elite controls literacy |
| `w_novelty` | tolerance for the new as such |
| `w_magic_fear` | how dangerous it is to produce an inexplicable effect |
| `w_religious_rigidity` | how much doctrine constrains inquiry |
| `w_commerce` | how much merchants are respected and protected |
| `bribability` | how far money buys a legal outcome. THIS IS A PROTECTION, and the old model had nothing like it. |
| `patronage_weight` | how much a powerful protector matters |
| `adaptation_rate` | how fast the astonishing becomes ordinary. People habituate. The iPhone was astounding in 2007 and boring by 2012. |

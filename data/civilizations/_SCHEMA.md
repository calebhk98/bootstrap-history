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
| `standing_army` | Soldiers the state keeps in pay at the start date, an initial condition like `population`; the state holds the same share of its people as the population changes. Its pay, equipment and the staff it draws from the labour pool are the state's budget (`sim/engine/actors/budget.py`). Missing means no standing force. Carries a source and confidence under `_internal`. |
| `currency_words` | `{"long": ..., "short": ...}`: how the money reads in a sentence ("you have 400 ___") and in compact lines. Absent: the `currency` field is used. |
| `currency`, `price_index`, `wage_index` | economy scaling. 1.0 is Rome 100 AD, which is the calibration baseline for `prices.json`. |
| `coin_standard` | **Required.** `{material, kg_per_unit, source}`: what one unit of the civilisation's money stands for physically, e.g. the silver in a denarius. Money is anchored to it: a labour hour is worth the reciprocal of the coin's solved labour hours. The material must be priceable with the civilisation's starting technologies, or loading fails. |
| `starting_interest_rate`, `starting_tax_share` | **Required.** Yearly rate on arrears, and share of a household's revenue taken by tax and dues, at the civilisation's start date. Initial conditions, held constant for now; a missing or non-numeric value is a load error. Each carries a source and confidence under `_internal`. |
| `state_revenue` | List of the forms of revenue the state raises: `form` (name), `basis` (a base the engine models: `harvest`, `adult_labour_years`, `imports_value`, `exports_value`, `coin_stock`; see `sim/engine/actors/revenue_bases.py`), `rate` (share of the base), optional `paid_in` (a material; the share is taken in kind, so the basis must yield that material), and `_internal` with a source and confidence. Absent means the state raises nothing. `starting_tax_share` no longer sets state revenue; it remains the ordinary share on a visible household. |
| `state_capacity` | 0 to 1. Can the state fund and compel a large project? Rome 0.85, Norse 0.15. |
| `starting_techs` | **Required, exhaustive, duplicate-free** node ids the civilization already has, including its material and capability nodes. Every id must exist in the universal graph or scenario loading fails. The engine never infers ownership from tier, cost, or another civilization's prerequisites: a zero-cost/tier-0 node absent from this list remains unknown. A different civ has a different free list. |
| `prerequisite_gaps` | `{node_id: reason}`: held nodes whose own `pre` the civilisation does not hold. `validate` errors on an undeclared gap; the reason `"unreviewed"` only warns. Write a real reason only where the history is clear, with its source. |
| `home_regions` | which geography regions it controls or trades in cheaply |
| `base_reach` | how far its ships and caravans already go, on the geography reach scale |
| `institutions` | which legal vehicles exist: partnership, corporation, guild, testament, charter, bank, patent |
| `values` | the REACTION MODEL. See below. |
| `hazards` | dated shocks: plagues, invasions, dynastic collapse, with year ranges. A `staff_loss` hazard now also costs the whole society population (`Sim.pop_deficit`, core.py), which raises `wage_index` until it recovers - see `_demographic_recovery` in core.py. Keep each civilization's list spread across its whole playable span (roughly every 50-90 years, start to start+700): a list that goes quiet for centuries reads as the game having stopped, not as a peaceful age. An optional `condition` on a hazard (resolved by `SocietyMixin._resolve_hazard_condition` in society.py) says whether ITS OWN NAMED CAUSE still holds given what the player has built: `{"field": "<one of staff_loss/sack_chance/output_factor/real_erosion>", "requires_all": [<tech ids>], "outcome": "avert"\|"alter", "alter_scale": <0-1, alter only>, "met_message": "...", "unmet_message": "..."}`. Only ever add one to a hazard whose `note` names a MATERIAL cause (a supply line, a building material, a drainage engine) that a household's own building plausibly removes - never to a succession, a religious policy or an administrative reform, which fire on schedule regardless of what one household built, exactly as history did. Both messages are mandatory: an averted or altered hazard that says nothing is indistinguishable from one the game forgot to fire. |
| `cost_multipliers` | what this society finds harder or easier than Rome, by node category and trait. Above 1 is dearer here. |
| `handicap_remedies` | per `cost_multipliers` key: `{"node": ..., "residual": ...}`. Building that node drops the multiplier to `residual`. |
| `briefing_absent` | `[{"claim": ..., "nodes": [ids]}]`: what the civilisation's briefing says it lacks; `validate` errors if `starting_techs` holds any of the nodes. |
| `needs_first` | HARD gates, as against the soft ones above: `{"<label>": {"node": ..., "because": ..., "ids": [...]}}`. Those ids cannot be STARTED at all until `node` is done, and the refusal quotes `because`. For what is not dear here but impossible - the Mexica had no draught animal of any kind, so a horse collar is not a 1.3x agriculture cost, it is nothing you can build. Always liftable by the node it names. An entry may also carry `material` and `units`: the gate then lifts as soon as that much of the material is held, however it came (see `opening_stock`). |
| `opening_stock` | `{material: units}`: living stock (silkworm eggs, a founding herd, planting stock) the civilisation holds at its date, credited to the held-stock ledger at the start. A node whose `holds` names the material opens only while it is held. Initial conditions only. |
| `will_not_sell` | `[material]`: goods this civilisation, as a trade partner, will not sell abroad (eggs of a monopoly crop). The foreign trade and a purchase from it both respect it. A transitional field: an actor-based export policy (`sim/engine/actors/policy.py`) would replace it. |
| `state_pressure` | How THIS state leans on a household once it is large enough to be worth leaning on - read by `SocietyMixin.requisition_report`/`office_report`/`military_demand_eligible`/`confiscation_risk`/`state_pressure_report` (society.py), gated everywhere on `state_notice()` (`state_capacity` times how large and visible the household already looks - see that method's own docstring). `requisition_name`/`office_name`/`military_name`/`confiscation_name` are the words a log line or `risk` uses for this civilisation's version of each; the matching `*_note` is the historical grounding; How much of a year's revenue the state takes is not set here: it follows the state's unfunded need (`sim/engine/actors/budget.py`). Requisition is bargained down by `protection`; office is not - it is compulsory, and gives protection back instead, see `update_protection`. Each civilisation has its own words for each: Rome's annona and munera, Han's salt and iron monopolies and corvee, English purveyance, what is owed at the Norse thing, Mexica tribute. |
| `notes` | what a newcomer must know |

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

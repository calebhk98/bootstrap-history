# Sugar is most of Rome's food, because it opens cheap

**Status:** partly done. Sugar and maize no longer reach a Rome opening (`python3 -m sim.tests --only sugar_maize_knowledge`). Open: `fat_kg` now takes most of the food units (532), so grains are most of the rest, not of the whole; cane labour and yield are order-of-magnitude figures.

Found sizing herds for 532: at a Rome opening (`opening.open_economy(build_setup(unopened_sim(civ="rome_100ad")))`),
`mat_sugar` is priced at a fraction of a denarius per kilogram and supplies most of the food need's units; millet,
olive oil, maize, wheat and wine make up most of the rest. Rome had little cane sugar; honey and grape must
sweetened, and grain fed people. Maize in Rome is a second error of the same kind.

Why it matters: households buy the cheapest calories, so a mispriced or misplaced crop sets what a whole society
eats, sizes its farms and its labour, and moves every price that follows (4.1: the diet must fall out of where
crops grow and what they cost).

What it would take: find why sugar opens so cheap at Rome (its recipe's labour and land, its climate gate: cane
needs a frost-free tropical or subtropical season, as 531 did for olives and cotton; whether `mat_sugar` is cane
sugar or a stand-in), and why maize grows in an Old World start (a knowledge gate, as 531 found for Mexica's olives).
Test: a Rome opening's food units come mostly from grains, with sugar and maize near nothing.
Related: 531, 532.

## Measured cause

Rome holds neither `ag2_sugar_voyage` nor `fud_maize`, and no producer runs `mat_sugar` or `maize_kg` at its opening
(the gates and the missing climate were already doing their job on supply). The units were demand with no supplier.
`long_run_costs` costs a good one technique beyond the held set ("gated"), `opening_costs` seeded that cost as an
opening price, and the household basket mixes goods on cost per need unit, so a priced good nobody could make drew
demand. Cane was cheap per food unit because its recipe charged 150 labourer-hours a hectare (borrowed from wheat,
leaving out the mill and boiling house) for 2000 kg of sugar, against grain at a few hundred kg a hectare.

Rome's food units, opening basket (script: `unopened_sim` -> `build_setup` -> `open_economy`, `opening_basket`
times the `food` effectiveness in `needs.json`):

| good | before | after |
|---|---|---|
| mat_sugar | 41.8% (0.12 a food unit) | 0 |
| fat_kg | 40.6% | 73.6% |
| millet_kg | 5.3% | 9.6% |
| olive_oil_kg | 3.7% | 6.7% |
| maize_kg | 3.0% | 0 |
| wheat_kg | 1.7% | 3.1% |
| wine_common_kg | 1.5% | 2.8% |
| flour_kg | 1.1% | 1.9% |

## Done

- `mat_sugar` carries `grown_in_climate_classes` (Af, Am, Aw, Cwa, as the cane nursery) and 1500 labourer-hours
  (conf D, from memory, not opened).
- `opening_costs` seeds no price for a household good that only a not-yet-held technique makes; a partner's price or
  a founder's research brings it in. Knowledge stays `requires_node` and `starting_techs`; no civilisation is named.
- Maize needs `fud_maize`, which only Mexica starts with (tested). Maize itself is agronomically fine in Rome's
  climate, so a climate list cannot exclude it: that is the knowledge gate.

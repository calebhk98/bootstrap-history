# Industrial Pollution (`bh_pollution_t9c3`)

Pollution derived from what the economy physically ran, not from an industry penalty. Feature request:
`Complaints/closed/108-add-industrial-pollution-and-externalities.md`.

## Turning it on

Nothing changes in a game until the player opts in. The mod ships Python, so it runs only after

    python3 sim/simulator.py mod-allow bh_pollution_t9c3

and then adds one command, `bh_pollution_t9c3:pollution` (agent protocol: `{"cmd": "bh_pollution_t9c3:pollution"}`).
It adds no technology, recipe, civilisation, need or constant, and overrides nothing.

## What it models

1. **Emissions.** Last year's producer runs times each recipe's inputs and outputs, in kilograms, times the
   per-kilogram factors in `data/pollution/emissions.json`: sulphur dioxide and ash from coal burned, acid mine
   drainage from coal mined (pyrite oxidation), sulphur dioxide from smelting copper, lead and mercury ores, lead fume,
   and mercury vapour from roasting cinnabar. Sulphur factors are stoichiometry (molar masses) of the sulphide the
   recipe names; each entry carries `derivation`, `source`, `conf`.
2. **Exposure.** A steady-state box (rate over wind speed times mixing height times airshed width) over the tile's
   settled airshed (its people times land per person, capped at the tile).
3. **Harm.** Excess deaths by age band from fine particles (Pope et al. 2002 slope times the band's baseline
   mortality from `sim/world/demography.py`); crop yield loss from SO2 above the UNECE critical level for crops.
4. **Counters.** Cleanup technologies in the tree reduce what escapes: electrostatic precipitation
   (`el2_electrostatic_precipitation_dust_collection`) for ash and lead fume; the flue dust collection of
   `zinc_industry_scale` for lead fume. The `abatement` list is data, so another mod can add its own file.
5. **Drivers.** Each tile row lists which source (coal burned, coal mined, copper smelted, ...) made each kilogram.

## Labelled heuristics (all in the data file, each with `retire`)

Sulphur fraction of coal (one coal everywhere); share of ash carried up the flue; pyritic share of coal sulphur; share
of smelter sulphur released to air; lead fume fraction; wind speed and mixing height (one climate everywhere); land per
person that sets the airshed; precipitator efficiency applied to every works at once; the SO2 yield-loss slope.

## Known limits

- **It acts on the game through `api.externality`:** its deaths join the year's epidemic deaths and its yield factors
  scale land-bound producers and the pooled harvest the people eat. A world phase also keeps each tile's particulate
  concentration and yield factor in tile stores, so `map layer <store>` shows them. The providers run twice a year
  (deaths, then yields) and the phase a third time, each recomputing the picture; none caches.
- Household fires (wood, peat, charcoal in homes) are not producer inputs, so domestic smoke is missing; charcoal and
  firewood burned by works carry no factor yet.
- No water model: acid drainage and mercury are loads by tile and do no harm. The tree has no scrubber or lime
  neutralisation node, so SO2 and acid drainage have no counter. Lead and mercury harm is occupational and needs workers'
  hours the economy does not expose.
- One airshed per tile (an upper bound where a tile holds many towns); emissions in the tile that makes them, no transport.

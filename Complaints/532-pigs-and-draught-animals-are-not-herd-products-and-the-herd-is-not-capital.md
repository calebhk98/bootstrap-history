# Pigs and draught animals are not herd products, and the herd is not capital

**Status:** partly - sheep, goat and cattle herds make wool, milk, meat, hides, tallow and horn jointly; pigs, draught animals from the herd, herd as capital and a non-mass cost split remain

**Done.** `data/production/95_herds.json` (one batch of 100 head-years each) from the species rows in
`data/world/living_stock.json`, gated on holding the herd (nodes `fud_sheep_flock`, `fud_goat_herd`, `fud_cattle_herd`; Rome,
Han, England and Norse hold them, Mexica does not and the expedition `exp_import_draught_animals` grants them). `meat_kg` is
a food good. Test: `sim/tests/test_herd_joint_products.py`. Complaints 365 and 366 (living stock as research, breeding) are closed.

**Open.**

- Pigs have no herd recipe (`grep -n pig data/world/living_stock.json` is empty).
- `draught_animal_kg` (`data/production/94_agri_organics_gaps.json`) is its own recipe (fodder inputs, `herder` hours), not a
  product of the herd model, so a draught animal does not come out of the same breeding stock as the herd's wool and meat.
- The herd is gated and bred but not charged as capital.
- Cost is split among outputs by mass, which prices wool and meat per kilogram alike and lets the milk-dominated goat recipe
  set the meat price (retire with 507).
- Most figures are recalled, confidence D; each row's `source` says which were read.

**Why it matters.** A good made jointly is mispriced when made alone (the schema's own example is lead and silver from
galena): wool expanded without more hides or meat, or a society with no animals still making tallow and parchment.

**What it would take.** A pig recipe from the same species rows; draught animals as an output of the herd's stock; the herd
as capital with a service life and replacement; a cost split by value (the economy's prices) in place of mass.
Pasture and salt inputs are 535 and `sim/geography/food_pasture.py`.

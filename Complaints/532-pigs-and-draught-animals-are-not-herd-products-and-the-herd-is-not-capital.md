# Pigs and draught animals are not herd products, and the herd is not capital

**Status:** partly - pigs, oxen as a herd product and the herd as capital are done; mules and horses, a value-based cost split and sourced figures remain

**Done.** `data/production/95_herds.json` (one batch of 100 head-years each) from the species rows in
`data/world/living_stock.json`, gated on holding the herd (nodes `fud_sheep_flock`, `fud_goat_herd`, `fud_cattle_herd`; Rome,
Han, England and Norse hold them, Mexica does not and the expedition `exp_import_draught_animals` grants them). `meat_kg` is
a food good. Test: `sim/tests/test_herd_joint_products.py`. Complaints 365 and 366 (living stock as research, breeding) are closed.

**Done (pigs, oxen, capital).** `lard_kg` in `data/production/95_herds.json` is the pig herd (pork `meat_kg`, `lard_kg`, `hide_kg`, dung) from the new `pig_kg` row in `data/world/living_stock.json`, gated on node `fud_pig_herd` (held by Rome, Han, England and Norse; Mexica declares `lard_kg` unsupplied). `lard_kg` is a food good in `data/world/needs.json`. Sources opened: Varro, De re rustica 2.4 (sows farrow twice a year, eight piglets fed, ten boars to 100 sows) and Oyieng, Marshall and Gauly, Uganda smallholder pig survey (7.1 weaned a sow-year). Live weight, dressing, lard share, stocking, sow share, loss, ration and dung are labelled heuristics (retire: Complaints/646). The cattle herd now gives oxen: `draught_share_of_offtake` of the offtake is kept to work, so `draught_animal_kg` is a joint output of `meat_kg`'s recipe and the carcass goods fall by that share (the share is a labelled heuristic). Every herd recipe carries a `capital` item: the herd held (`herd_stock`), service life one over the row's `annual_loss`, priced at the live-weight recipe, so deaths are charged as wear. Tests: `sim/tests/test_herds_pigs_draught_capital_and_chain_goods.py`.

**Open.**

- Mules and horses are still `draught_animal_kg`'s own recipe (`data/production/94_agri_organics_gaps.json`, fodder inputs, `herder` hours); oxen come from the herd, so the two routes now both make the good. Retiring the own recipe needs a mule row (ass and mare breeding stock) and the stock growth of `draught_animal_kg` read from herd output.
- Bristle is not made: nothing consumes it and no yield figure was found.
- Cost is still split by mass (retire with 507); `allocate_joint_cost` already takes reference prices and the test shows the value split, but no reference price is supplied to the herd's outputs, and no source for relative values was found.
- Capital is charged by deaths only (loss x herd value with interest); the herd's own births are not an input. Whole-game effect not measured (`economy-check` and the openings were not run).
- Most figures are recalled, confidence D; each row's `source` says which were read.

**Why it matters.** A good made jointly is mispriced when made alone (the schema's own example is lead and silver from
galena): wool expanded without more hides or meat, or a society with no animals still making tallow and parchment.

**What it would take.** A pig recipe from the same species rows; draught animals as an output of the herd's stock; the herd
as capital with a service life and replacement; a cost split by value (the economy's prices) in place of mass.
Pasture and salt inputs are 535 and `sim/geography/food_pasture.py`.

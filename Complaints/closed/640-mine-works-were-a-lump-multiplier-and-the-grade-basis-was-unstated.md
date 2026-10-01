# Mine works were a lump multiplier and the grade basis was unstated

**Status:** closed - barren rock, hoisting, carrying, drainage, timbering and ventilation are separate physical terms (`sim/world/mine_works.py`); the remaining gap is 641

Opened sources: Bettenay 2022 (Metalla 26.2, Tables 2-4, local text), Agricola De re metallica (Hoover translation, Project Gutenberg), Diodorus 5.36-38 (Thayer). Not opened: Strabo 3.2.10 as text (only the figures quoted in 410), Pliny NH 33 (only the passages Agricola's notes quote), Hopper, Davies, Domergue, Conophagos, Kongsberg originals (only Bettenay's tabulation).

## Decomposition of Bettenay's realistic Melle model (Table 4, notes)

- Face: 100 miners, 150 kg rock per miner-day, 300 days. Half the rock is ore presented for dressing (note 3), the rest barren (shaft sinking, drives, face waste, dilution, discards; note 4).
- Ore grade 6 percent galena as presented (5 percent Pb); 43 tonnes of ore per tonne of lead after the recoveries in notes 6-10.
- Mine staff: face miners and fire-setters are 40-70 percent of mine staff, the rest underground or surface support (hauling, ventilation, water, timber, wood to faces). Processing staff about equal the mine staff; forest about a third of the total.
- All-in, 250-300 workers for 150 kg of silver: about 4,400 hours per kg; Table 3's Early Modern districts give about 1,000-1,700.

## Grade basis

`ore_grade_kg_per_tonne` is metal per tonne of ore as presented to dressing, not per tonne of rock broken: the entries' own sources call them ore grades, and the lead recipe dresses that ore. Rock broken per tonne of ore is higher by the barren share. The grade values themselves are unchanged and unsourced (641).

## What is charged now

Per tonne of ore, by depth class: breaking and fire-setting every tonne of rock broken (ore over an ore share of 1.0 / 0.65 / 0.5 for surface / shallow / deep, Bettenay Table 4); hoisting (physical lift from the shaft depth); carrying (100 kg barrow, round trip over a haul distance per class); draining (water lifted the whole head, inflow per tonne of ore per class); timbering (geometry, share timbered by rock hardness); a ventilation shaft per working shaft in the build cost. The unsourced lump multipliers on breaking hours are gone. The shift is Agricola's seven hours (Book II). Applied to every vein and surface deposit: iron, copper, lead, silver, mercury and Dacian gold; alluvial tin and gold unchanged.

## Result (`python3 sim/solve_prices.py --civ rome_100ad --why silver_kg`)

Silver about 335 to 379 hours per kg; gold to silver ratio about 40 to 35 (gold unchanged); lead about 1.28 times; copper 1.04 times; wheat, cloth, charcoal and the Roman iron bar unchanged (Han iron bar 1.01 times).

# Silver chain does not yet charge for what a mine and a smelter actually do

**Status:** open

Rome's silver solves at about 319 labour hours per kg (`python3 sim/solve_prices.py --civ rome_100ad --why silver_kg`) against about 3,700 hours per kg from Strabo's 40,000 workers and Polybius's daily revenue (see 410). Grade is not the gap (410's update). The physical items the recipes still leave out, each needing a source before a number moves:

- (Fire-setting wood is now charged for hard rock, see 610.) Fire-setting wood and mine lighting, ventilation and timbering consumed per tonne of rock (Pliny NH 33.71, Agricola book VI); only breaking, haulage and a shaft's build are charged (`sim/world/deposits.py`).
- Slag: smelting leaves slag carrying lead that was re-smelted, and slag mass handled per tonne of lead (Rio Tinto and Laurion slag heaps).
- Washing and crushing labour per tonne of rock is one conf D figure; the direct silver recipe (`silver_kg`, patio route) charges about a twentieth of the lead route's dressing rate per tonne of rock for the same work. Align them once a source gives crushing throughput.
- Fuel for roasting, hearth lining wear and bellows labour per tonne of lead (Agricola book IX).
- Mine owner's and state's claim: not a recipe matter (see 410).

Do not move any figure to reach the attested day wage (CLAUDE.md 4.1).

## Update (mine-labour-per-tonne)

Labour per tonne of rock checked against Kongsberg and Melle figures and fire-setting wood added to hard rock; silver moved from about 319 to about 335 hours per kg and the gap remains. See 610, 611, 612.

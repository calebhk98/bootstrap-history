# Recipe need shares overweight mining and leave out transport and much of building

**Status:** partly - need shares include carters, a water need met by carried, well and piped water (plumbers), millwright hours where shaft work is drawn, spending split by labour value per unit of need, and no generic weight for end goods nobody demands. Remaining: land carriage is charged over a stated mean haul (`MEAN_HAUL_KM`), which makes carters about a quarter of Rome's non-farm need; the haul must come from the distances goods actually travel between where they are made and used. Potters, glassblowers, scribes and engravers now fall to the floor because no need names vessels, glass, writing or coin; those needs (or the recipes that use the goods) must exist so these trades get the demand they had in history

The labour package now sizes each trade's town and national population from its share of non-farm
labour need. The source is `workforce_spinup.need_shares_by_trade` (the recipe graph under an equal
budget split), replacing hand-written "density classes".

For Rome, this command shows the result:

    python3 -c "from sim.tests.harness import sim; lab=sim(civ='rome_100ad').labour; print(sorted(((round(v,3),k) for k,v in lab._non_farm_need_shares().items()), reverse=True)[:8])"

- Mining takes about half of all non-farm need, and artisans and furnacemen most of the rest.
- Sailors, plumbers and millwrights have no recipe demand at all, so they fall to the declared floor
  (`NO_DEMAND_TRADE_SHARE`). That is about one person in the home town and a few hundred in the empire.
- Sailors are kept up only by the rule that trades in the farm trade's registry family draw on the
  unskilled pool (`labour_population._is_unskilled_pool`). Plumbers have no such rule.

Why it matters: an empire with a Mediterranean fleet and lead water pipes has almost no sailors or
plumbers to hire, and every concern that needs them is starved. The derivation is right in kind. What
is missing is the demand behind those trades.

What it would take:
- Demand for transport (freight and ships) and for building services (pipe, mills, houses) in the
  household need basket and the recipe graph (`data/world/needs.json`, `data/production/`).
- Spin-up budget weights from need data rather than an equal split (`sim/labour/workforce_spinup.py`
  docstring heuristics).
- Then `NO_DEMAND_TRADE_SHARE` should apply to almost nothing.

Measured cost of the gap (main against this branch, rome_100ad, `population` figures): plumbers fell from
about 109,000 nationally and 700 within the founder's reach to about 181 and 1. The water-works and
plumbing technologies (`cn_siphon`, `cn_water_main`, `ben_civic_water_works`, which state plumber hours)
are therefore much slower to staff in Rome. A neutral prior (unknown demand read as the family's median
share) was tried and rejected. It restores Rome's plumbers but also gives Rome and the Mexica tens of
thousands of millwrights, against the registry's own notes. The fix is data:
- lead pipe and water-works demand in the recipe graph;
- or the civilisation file stating the trades already established there, an initial condition
  CLAUDE.md 4.1 allows.

Owner decision (2026-10-09): comes after 119 and 135. Once transport is costed properly, demand for shipping and carriage should rise by itself; prefer that to stating the demand.

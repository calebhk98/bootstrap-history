# Most ancient occupations have no trade, and their hours are booked as farming

**Status:** open - umbrella; remaining children are 613 and 619 (closes when they do)

An outside list of the twenty commonest occupations in classical civilisations (Rome, Greece, Mesopotamia, Egypt) was
checked against the trade registry (`data/world/trades.json`) and the `labour_hours` of `data/production/`. The list is a
validation reference under CLAUDE.md 4.2, not a target to hardcode.

## Children

Done (closed): 609 (farm trade separate from the unskilled fallback: `FARM_TRADE` is now `farmer` in
`sim/labour/legacy_trade_defaults.py`), 610 (spinning, weaving, fulling, dyeing), 611 (herding, milling), 612 (tanning,
charcoal, lime, salt), 614 (bread, oven, bakery), 615 (fish as a good, salted fish, garum), 616 (wine, oil, jars), 617 (ships
and shipwrights), 618 (Mexica stone tools, obsidian knappers).

Open:

- 613: porters and dockworkers are invisible labourers. Land carriage on foot is a route mode
  (`sim/geography/routes_rates.py`, `_porter`) whose hours are `labourer`; in a society without draught animals porters
  were one of the largest labour groups.
- 619: no baseline check (CLAUDE.md 4.2) that the occupational distribution of a Rome run falls in a plausible range (most
  households on the land, textiles and building among the largest non-farm trades). Measure what exists with
  `python3 -c "from sim.tests.harness import sim; lab=sim(civ='rome_100ad').labour; print(sorted(((round(v,3),k) for k,v in lab._non_farm_need_shares().items()), reverse=True))"`
  and `lab.farm_share_of_hours()`; they measure different things (hours needed against where people lived and what they
  called their work), so a gap to the reference's farm share is not by itself a defect. The seasonal by-employment of a
  peasant household (spinning, weaving, herding, carting, building) has no place in the model; see 645 and 542.

## Decisions (answered)

- Domestic service, cooks and tavern keepers come from household work as a need met by own hours or hired (645).
- Religion is out of the base game and left to mods (`mods/TASKS.md`); priests and diviners wait on a mod.
- Han salt and iron monopolies and the state iron workforce are 492. Seasonal labour and corvee are 542 and 600.

## Not filed

India (caste, cotton weaving) and Egypt have no civilisation in `data/civilizations/`; nothing to file until one is added.

## Update (619 pass)

`sim/tests/test_occupational_hours_rule.py` (quick) now holds the rule that the occupational shares are each group's hours
over all hours with every employer's staff counted once, and that a list of named crafts' recipes never bill only
`labourer`. Waste haulage and natron were rebilled to porter, carter and salt worker. The remaining `labourer` recipes are
crushing, digging, quarrying and hauling work; whether any of them should name a trade is an open question for the
sourced trade notes. Re-measure Rome with the slow topic before closing 619.

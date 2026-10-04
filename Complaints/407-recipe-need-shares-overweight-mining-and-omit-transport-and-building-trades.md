# Recipe need shares overweight mining and leave out transport and much of building

**Status:** open

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

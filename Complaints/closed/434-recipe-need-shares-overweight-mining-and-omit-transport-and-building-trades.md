# Recipe need shares overweight mining and leave out transport and much of building

**Status:** closed - carriage, water-pipe, shelter and shaft-work labour all enter the need shares through the recipe graph, spin-up budgets follow the needs' surplus_budget_share, and grain is milled before it is eaten so water-mill millwrights have demand; the one item left in the economy's pricing is filed as Complaint 472

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

## Closing record

Measured without a game: call `workforce_spinup.need_shares_by_trade` on the loaded recipe data (`sim/tests/test_need_shares_milling.py` does this per civilisation). Before this closing, Rome: furnacemen 0.31, miners 0.25, sailors 0.16, carpenters 0.08, carters 0.03, plumbers 0.004; millwrights 0 for every civilisation including England 1300. Carriage (the carter and sailor trades, workforce_carriage.py, the hours a tonne's value pays to haul), piped water (the plumber's hours and the lead pipe's build bill), and shelter (masons and carpenters) already reached the shares through the recipe graph; the budget between needs already follows each need's `surplus_budget_share` (`need_demand.budget_weights_by_good`), with the mix inside a need by labour value, not an equal split (pinned by `test_a_need_s_budget_follows_its_surplus_budget_share_not_an_equal_split`).

What was missing was any household demand for shaft work, so a water wheel (`waterwheel_unit`, `mechanical_mj_waterwheel`, millwright hours) was in no chain. `data/production/95_grain_milling.json` adds milling of wheat, millet and maize into `flour_kg` (conf C estimates; shaft work priced through the energy market, as everything else), and `flour_kg` is a food in `data/world/needs.json`. England 1300 now has millwright demand, Mexica (no water wheel) none, and Rome gains it on reaching `cap_power_water`.

Trades still sized by `NO_DEMAND_TRADE_SHARE` in each civilisation at its start (the measurement command is `PYTHONPATH=. python3` over `need_shares_by_trade` and the registry, as in the test): master (a rank, named by no recipe), engraver (coin demand gives about two in a hundred thousand workers, below the floor), and millwright (the milling shaft work is a small share of hours, a few per million, below the floor); plumber where there is no lead plumbing and glassblower where there is no glass, which are absent by technology. The neutral prior the earlier text rejected is not used. The floor now applies to rank and near-zero trades, not to the empire's fleet, carriers or plumbers.

Vessels: `sim/tests/test_economy_vessel_price_fixture.py` runs a small economy (a vessel durable fired from dug clay, 40 years) and the vessel's price stays within a few times its opening price and above its input cost, so the thin-market ceramic runaway is not reproduced there after Complaints 336, 398, 468 and 470. The fixture does show the dug input's price swinging by roughly ten times from year to year; the full-game ceramic price (13 against 1.04 at the opening) could not be re-measured here (building a Rome game cold takes over ten minutes). Both are filed as Complaint 472.

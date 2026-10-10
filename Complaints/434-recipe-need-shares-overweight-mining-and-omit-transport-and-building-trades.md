# Recipe need shares overweight mining and leave out transport and much of building

**Status:** partly - everything in the earlier closing line holds (carters, water, shaft work, vessels, writing, coin, substitute-capped wages, durables opened in use). Open: vessels are still dear in a long game. Inputs now open beside their users (`opening._place_producers` places a supplier by the demand of the producers that use its good), which took the most populous tile's vessel cost from about 85 to about 17 a person a year against food at about 43, but ceramic still clears near 13 against 1.04 at the opening. The cause left is in the economy's long-run price and entry dynamics for thin low-value markets, not the opening: over a 30-year spin-up sold-out sellers raise asks faster than their output follows (clay and firewood at 40 to 50 in tiles without a local supplier; piped water drifts dearer than carried water, so plumbers are trimmed from about 590 to about 15 and the water floor falls on carried water that was sized for a twelfth of it). It needs the seller-pricing and entry rules (`sim/economy/seller_pricing.py`, `seller_offers.py`; Complaints 398 and 468, both closed, built the first part), not this complaint's data. The vessel floor (5 kg held, 4 year life, Deal 1998 recalled) is unchanged; no better-sourced figure was found offline.

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

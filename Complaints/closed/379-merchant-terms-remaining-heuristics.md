# Merchants' terms still rest on labelled guesses

**Status:** closed - the merchants' terms are derived: crew is the rig's need plus the defenders worth their keep,
provisions are carried between restocking places, routes are chosen with provisions charged, and the markup,
agents, houses, wait, class capital and retention follow from the destination's price response, the labour
market and the capital market (the one number left, `RESTOCK_INTERVAL_DAYS`, is a declared heuristic).

What closed it, in `python3 sim/constants.py --burndown` terms (no `MONOPOLY_MARKUP_SHARE` or `AGENTS_PER_CARRIER` left):

- Crew as a choice: `sea_freight.defenders_to_hire` signs on the hands whose keep is less than the
  expected loss of hull and cargo they prevent (`PIRATE_BOARDING_PARTY` and the meeting rate stay labelled);
  the carrier model and the loss rate use that crew (`_sea_crew` in `sim/engine/foreign_routes.py`).
- Markup: `merchant_terms.monopoly_markup_share` from the destination's price flexibility (the agent economy's
  response for the good at home, else the market's own clearing with a cargo added), over the houses on the route.
- Agents and houses: `sim/world/merchant_house.py`; a house owns the carriers its capital buys, keeps a factor at each
  end shared among them, and the labour market caps the houses it can staff.
- Wait: `selling_years` into the destination's demand, `season_wait_years` from the sailing days.
- Capital: the class holds its wage-bill share of the funds households put in the pool; its borrowing is a loan in
  `market_loans`. Retention: the share of the markup kept is the part of merchants' return above the market rate.
- Provisions: `provisions.restocked_share`, a land carrier restocking every `RESTOCK_INTERVAL_DAYS` of travel and a hull
  at the leg's ends; no floor, and a stage the carrier cannot provision is impassable. Routes are searched on rates
  divided by the share delivered (`sim/engine/foreign_route_choice.py`) and the cheapest priced route kept.
- Tests: `test_merchant_derived_terms` (quick), `test_freight_provisions` (grain reach, land short and sea far);
  `test_merchant_terms` (whole game, slow) was updated and not run in this change.

Left labelled elsewhere, not here: `MERCHANT_DENSITY` is the merchants' headcount estimate in `sim/labour`, no longer
a capital figure; `RESTOCK_INTERVAL_DAYS`, `PIRATE_BOARDING_PARTY`, `PIRATE_ENCOUNTERS_PER_THOUSAND_KM` stay
`temporary_heuristic`.

Complaint 346 derived merchants' wait, agents' cost, markup, speed and capital from the fleet,
the labour market and the capital market; this one removed what was left stated.

## Evidence

`python3 sim/foreign_trade_report.py --years 100 --partner han_china_100ad` (script since removed; recover with `git show 97473f1:sim/foreign_trade_report.py`): cloth imports rise
to thousands of tonnes a year as the fleet grows, limited by lift, not by capital; compare the
earlier figures in `Complaints/346`.

Related: 346, 339.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 346 (`closed/346-merchant-terms-and-ornament-limit-are-heuristics.md`): merchant terms are derived; the remaining heuristics are listed here, ornament held stock is in 442.

Owner decision (2026-10-09): derive the merchants' terms instead of stating them: crew per ship from what the ship needs to sail and defend itself, food and water for the crew and animals over the voyage, the mass of the cargo and of the coin carried to pay for it, and the risk of robbery against crew size. Done right, heavy cheap goods (grain) only move a few tiles by land, because the carriage or the animals' feed eats the value, while a ship moves the same grain much further at a lower cost per kg.

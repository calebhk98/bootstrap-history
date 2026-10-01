# Gold solves cheaper than silver, so households' ornament budget buys gold

**Status:** partly - gold_kg's placer labour was a thousand times too low (a per-tonne entry holding a per-kilogram figure), so gold solved at about 40 labour hours per kg against silver's 319; with it corrected gold solves at about 13,400, above silver, so the ornament budget no longer picks gold. Still open: a deposit-based or supply-limited gold price (571)

The ornament need in `data/world/needs.json` treats the bright metals as
equivalent per kilogram, so households put the whole ornament budget on the
cheapest, and the solved price of gold is below silver's. A partner that cannot
make gold then wants a very large tonnage of it (`household_tonnes_by_material`
in `sim/engine/foreign_capacity.py`), which drains the exporter in foreign
trade. Related to `Complaints/410`.

## Evidence

`python3 sim/foreign_trade_report.py` shows gold among Rome's exports; compare
the solved gold and silver prices with `python3 sim/audit_costs.py`.

## What it would take

A gold price from a deposit model or a stated limited supply
(`supply_per_year` in `needs.json`), so gold clears at what its supply allows
rather than at labour embodied.

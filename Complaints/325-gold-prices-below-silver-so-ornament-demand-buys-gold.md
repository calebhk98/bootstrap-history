# Gold solves cheaper than silver, so households' ornament budget buys gold

**Status:** partly - the ornament need declares `satiation_per_capita_per_year` (a labelled heuristic: durable metal is worn and lost, not bought up to the budget share), so households' bright metal is a fraction of a gram per head a year instead of tens of grams, and the spending it frees goes to the other needs (`sim/world/need_satiation.py`); gold's own labour fix is kept; still open: a deposit-based or supply-limited gold price (334) and a held-stock model of ornament in place of the heuristic limit

The ornament need in `data/world/needs.json` treats the bright metals as
equivalent per kilogram, so households put the whole ornament budget on the
cheapest, and the solved price of gold is below silver's. A partner that cannot
make gold then wants a very large tonnage of it (`household_tonnes_by_material`
in `sim/engine/foreign_capacity.py`), which drains the exporter in foreign
trade. Related to `Complaints/305`.

## Evidence

`python3 sim/foreign_trade_report.py` (script since removed; recover with `git show 97473f1:sim/foreign_trade_report.py`) shows gold among Rome's exports; compare
the solved gold and silver prices with `python3 sim/audit_costs.py` (script since removed; recover with `git show 97473f1:sim/audit_costs.py`).

## What it would take

A gold price from a deposit model or a stated limited supply
(`supply_per_year` in `needs.json`), so gold clears at what its supply allows
rather than at labour embodied.

Owner decision (2026-10-02): if households were buying ornamental gold its price should have risen by itself; that it did not points to a bug in the market model.

# Derived concerns whose entries state no plant earn wages only

**Status:** open

Most output-derived nodes gate entries with no `capital` item, so the solver's plant return (`Complaints/319`) never applies and the node earns its staff's wages and nothing above. Stating a plant needs build materials, labour, a service life and a yearly capacity per entry, each with a basis (`data/production/_SCHEMA.md`); inventing them to lift a margin would be back-solving (CLAUDE.md 4.5). Count: the line `earning exactly their upkeep` in `python3 sim/node_revenue_report.py` (script since removed; recover with `git show 97473f1:sim/node_revenue_report.py`); which entries state a plant: `sim/tests/test_capital_charge.py`.

Related: `Complaints/319`, `Complaints/329`, `Complaints/283`.

Related: 140, 295, 317, 318, 336, 337.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 295 (`closed/295-energy-carriers-have-no-per-megajoule-price-for-node-revenue.md`): `en_*` power nodes need gated energy entries with plant capacity, and demand for energy, so they earn from output rather than typed-in revenue.
- 318 (`closed/318-nodes-with-production-entries-state-no-plant-staff-hours-or-output.md`): chemical and other nodes with production entries state no plant, staff hours or output; each needs a sourced throughput.
- 319 (`closed/319-a-concern-selling-at-cost-earns-its-staff-and-nothing-above.md`): a concern selling at cost earns only its staff: the capital charge is in the solver, the rest is capital stated in the entries (this issue).
- 329 (`closed/329-declared-outputs-bound-chemical-makers-but-solved-prices-break-their-payback.md`): declared outputs for caustic soda, glycerol and similar break payback at solved prices; corrected entries with sources needed.
- 337 (`closed/337-the-solvers-capital-charge-uses-the-starting-rate-and-leaves-out-inven.md`): the solver's capital charge uses the starting rate; needs the live rate (banded) in the cache key and a holding period per material.

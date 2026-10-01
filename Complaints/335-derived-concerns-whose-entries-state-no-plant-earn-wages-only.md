# Derived concerns whose entries state no plant earn wages only

**Status:** open

Most output-derived nodes gate entries with no `capital` item, so the solver's plant return (`Complaints/319`) never applies and the node earns its staff's wages and nothing above. Stating a plant needs build materials, labour, a service life and a yearly capacity per entry, each with a basis (`data/production/_SCHEMA.md`); inventing them to lift a margin would be back-solving (CLAUDE.md 4.5). Count: the line `earning exactly their upkeep` in `python3 sim/node_revenue_report.py`; which entries state a plant: `sim/tests/test_capital_charge.py`.

Related: `Complaints/319`, `Complaints/329`, `Complaints/283`.

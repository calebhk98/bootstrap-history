# Derived concerns whose entries state no plant earn wages only

**Status:** closed

Most output-derived nodes gate entries with no `capital` item, so the solver's plant return (`Complaints/319`) never applies and the node earns its staff's wages and nothing above. Stating a plant needs build materials, labour, a service life and a yearly capacity per entry, each with a basis (`data/production/_SCHEMA.md`); inventing them to lift a margin would be back-solving (CLAUDE.md 4.5). Count: the REVENUE and UPKEEP AND CAPITAL BASIS lines of `python3 sim/simulator.py validate`; which entries state a plant: `sim/tests/test_capital_charge.py`.

Related: `Complaints/319`, `Complaints/329`, `Complaints/283`.

Related: 140, 295, 317, 318, 336, 337.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 295 (`closed/295-energy-carriers-have-no-per-megajoule-price-for-node-revenue.md`): `en_*` power nodes need gated energy entries with plant capacity, and demand for energy, so they earn from output rather than typed-in revenue.
- 318 (`closed/318-nodes-with-production-entries-state-no-plant-staff-hours-or-output.md`): chemical and other nodes with production entries state no plant, staff hours or output; each needs a sourced throughput.
- 319 (`closed/319-a-concern-selling-at-cost-earns-its-staff-and-nothing-above.md`): a concern selling at cost earns only its staff: the capital charge is in the solver, the rest is capital stated in the entries (this issue).
- 329 (`closed/329-declared-outputs-bound-chemical-makers-but-solved-prices-break-their-payback.md`): declared outputs for caustic soda, glycerol and similar break payback at solved prices; corrected entries with sources needed.
- 337 (`closed/337-the-solvers-capital-charge-uses-the-starting-rate-and-leaves-out-inven.md`): the solver's capital charge uses the starting rate; needs the live rate (banded) in the cache key and a holding period per material.

## Closed

Re-measured after a node came to earn only from the output of the entries that name it in `operated_by` (`python3 sim/simulator.py validate`, REVENUE lines). Few nodes earn from output, so the concern shrank to those entries:

- Every entry an output-earning node runs now states a plant (build materials and labour, service life, yearly capacity, each with a `capital_basis` and a C or D grade). Capacities are the staff's where the entry's own hours bound the node, a physical size otherwise; where a plant of the physical kind would far outrun what the node's crew can work, the plant is taken at the size the crew runs. Extraction streams (`extracted_from`, no inputs) keep none, since a deposit or a parent stream sets their output. `sim/tests/test_capital_charge.py` (`OutputEarningEntriesStateAPlant`) fails if an operated entry has none or an item lacks a field.
- 295: the water wheel's energy entry is run by the undershot-wheel node; the engines, dynamo, motor, photovoltaic and mains entries already were, and now their machine-building entries state plants too. Nodes with no energy entry earn nothing rather than a typed figure. The one labelled heuristic that remains is in `sim/engine/energy_prices.py` (a producer sells no dearer than its own technique costs).
- 337: the incumbent price tables take the live market rate in a band (`prices.band_interest_rate`, `INTEREST_RATE_BAND`, keyed into the table caches in `incumbent_prices.py`), and an entry may state `holding_years` (with `holding_basis`) for the time its inputs are paid for before the output sells; the solver charges the market rate on them (`recipe_cost_and_allocation`). Leather (a year in the pits) and saltpetre (beds ripen) state it.
- 329: caustic soda, gunpowder, phosphoric acid, mirror amalgam, polyethylene and glycerol now state labour, a plant and an operating node. Glycerol keeps its labelled heuristic that the soap from the same batch is not credited: a joint entry with soap as a second output falls out of the solver's reach (`entries_in_reach` drops an entry whose co-product a nearer technique makes), which would leave glycerol unpriced.
- The charcoal tar kiln states the same hut and tools as the clamp, since the joint tar entry sets charcoal's price.

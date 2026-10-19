# Porters and dockworkers have no trade, so the largest labour group of a society without draught animals is hidden

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Depends on 609.

**What is wrong.** Land carriage on foot is a route mode whose hours are `labourer` (the `carter` note in `data/world/trades.json` says "porters on foot stay labourers"). Loading at ports was not traced. In a society without draught animals (the Mexica) porters were among the largest labour groups.

**Evidence.** `sim/geography/routes_rates.py` (`_porter`); `data/world/trades.json`.

**Why it matters.** The labour market never sees the demand for porters (see also 552).

**What it would take.** A porter trade for foot carriage and a dockworker trade for port handling, read from the route modes; trace port loading first and record it.

**Test.** A test: foot carriage hours are booked to the porter trade and show in the non-farm need shares.

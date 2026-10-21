# Porters and dockworkers have no trade, so the largest labour group of a society without draught animals is hidden

**Status:** partly - porter and dockworker trades exist and carriage books to them; a whole-game run with real porter workforces is not yet checked (see Done)

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Depends on 609.

**What is wrong.** Land carriage on foot is a route mode whose hours are `labourer` (the `carter` note in `data/world/trades.json` says "porters on foot stay labourers"). Loading at ports was not traced. In a society without draught animals (the Mexica) porters were among the largest labour groups.

**Evidence.** `sim/geography/routes_rates.py` (`_porter`); `data/world/trades.json`.

**Why it matters.** The labour market never sees the demand for porters (see also 552).

**What it would take.** A porter trade for foot carriage and a dockworker trade for port handling, read from the route modes; trace port loading first and record it.

**Test.** A test: foot carriage hours are booked to the porter trade and show in the non-farm need shares.

## Trace

Carriage hours reach the labour market through `sim/economy/carriage_hours.py` `Crew.hours_by_trade`: each mode's
`crew_trade` (from `data/world/geography/route_modes/modes.json` through `sim/geography/routes_carriage.py`) and crew
hours per tonne-km (`routes_rates._porter` for foot) become the setup's `carriage_crew`. Two things hid porters. The mode
data said `crew_trade: labourer` for foot. And `CARRIAGE_CREW_UNSKILLED_SHARE` (a labelled heuristic) bids every mode's
crew in the unskilled trade anyway. Port loading was a fixed `PORT_HANDLING_HOURS_PER_TONNE` for the sailing mode only,
always booked to the unskilled trade (`carriage_handling`).

## Done

- `data/world/trades.json`: new `porter` and `dockworker` trades (training 0: anyone can take them up at once; no
  sourced fatality rate, so zero with the absence statement).
- `modes.json`: foot `crew_trade` is `porter`; sail names `handling_trade: dockworker`. `routes_carriage` passes it,
  `EconomySetup.carriage_handling_trade` carries it, `Crew.hours_by_trade` books handling to it (unskilled trade when a
  mode names none). The heuristic share now applies only to modes whose trade asks more training than the unskilled
  trade, so porters and dockworkers are hired in their own name.
- `occupation_groups.json` transport group lists both.
- Test: `sim/tests/test_porters_and_dockworkers.py`.

## Sources

- Load and pace: https://en.wikipedia.org/wiki/Tlamemeh, read: tlamemes began young, "carrying on average 23 kilos" and
  a "daily commute of 21 to 25 kilometers". The foot mode's 27 kg and 22 km a day (research notes) sit near this.
  Secondary source; Hassig's book was not opened, so no Hassig figure is used.
- Port handling hours per tonne: no source found. A port-economics page gives a longshore crew 5 to 10 tons an hour but
  not the crew size, so no per-worker figure follows. `PORT_HANDLING_HOURS_PER_TONNE` stays a labelled heuristic.
- Not yet derived: the sea handling money (`handling_rates`) is still priced at the unskilled wage; porter and dockworker
  wages come from the labour market.

## For the PM (slow, not run)

`python3 -m sim.tests --slow --only occupational_distribution,carriage_hours --jobs 1`, and a multi-year mexica_1500 run
to see whether porter workforces form (the quick `economy-check --civs mexica_1500 --years 2` ran clean).

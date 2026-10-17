# No check holds freight to the historical sea, river and land cost ratio

**Status:** open

Reference (an outside design note, not code-aware): Diocletian's Price Edict implies roughly 1 by sea
to 5 by river to 28-40 by land for a tonne of grain.

## Measured

Physical cost per tonne-km (labour hours, feed converted) relative to coastal sailing, flat ground:

    python3 -c "from sim.geography import map_source, routes_rates as r; m=map_source.load_map(); t=r.rate_table(m); b=r.physical_cost(m,t.rate('sail','coast',0.02)); print({k: round(r.physical_cost(m,t.rate(k,e,0.02))/b,1) for k,e in (('river_boat','river'),('cart','land'),('pack','land'),('road','land'))})"

- River is closer to sea than the Edict ratio (still water; upstream legs differ).
- A paved road falls in the Edict range; a cart or pack train on an unbuilt edge is several times dearer.

The money rate (`sim/geography/freight_cost.py`, `freight_money_per_tonne_km`) adds carrier capital,
return legs and losses (Complaint 326, closed); its ratio was not measured here.

## What it would take

- A test that measures the money ratio for a Rome opening and checks it falls in a stated range (a
  validation under 4.2, not a tuning target), so a change to freight physics that breaks it shows.
- If the money ratio is also off, find which input is wrong (feed per tonne-km, cart load, pace)
  rather than scaling a mode.

## Second note from the same source

It claims the ratio emerges from physics alone (cart friction and feed, river drag, wind for sail plus
crew and hull wear). Freight here is already built that way (`sim/geography/transport.py`,
`sea_freight.py`), and the physical ratio measured above does not land on the Edict ratio. That is
the point of the check: find which physical input is off, do not scale a mode to the target.

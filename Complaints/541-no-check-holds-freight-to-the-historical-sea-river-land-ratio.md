# No check holds freight to the historical sea, river and land cost ratio

**Status:** partly - the physical ratio is now held by `sim/tests/test_freight_mode_cost_ratio.py`; the money ratio for a Rome opening is not yet checked

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

## Progress

`sim/tests/test_freight_mode_cost_ratio.py` reads the rates the route search uses (`routes_rates`) and
asserts bands (wide, because the Edict is one source of maximum prices with margins, risk and dues in its
sea and river figures, and its land figure is a road wagon): river 2 to 8 times coastal sailing, a built
road 10 to 60 times, a cart on dirt track 1.5 to 6 times the road, and the order sea < river < road < cart
< pack. Re-measure with the command above (flat or gentle grade; add a current for the river with
`t.rate('river_boat','river',0.0,-1.0)`).

Measured (labour hours with feed converted, relative to coastal sailing): river still water 2.6; river
against a 1 km/h current 3.8, against 2 km/h 7.7; built road 15 on flat ground, 37 at a 2% grade (Edict
28-40); cart on dirt track 62 flat, 115 at 2%; pack string 122 flat, 145 at 2%.

Findings:
- Land: the road lands in the Edict range at a gentle grade. It is grade-sensitive because a two-ox team's
  load falls steeply with grade; that is physics, not a data fault.
- River: still-water towing is about half the Edict figure. The inputs behind it are the towing
  resistance coefficient (`WATER_TRANSPORT_RESISTANCE_COEFFICIENT_AT_TOW_SPEED`, already a labelled
  temporary heuristic in `sim/geography/transport.py`) and a flat-water, no-current default. Nothing in
  the data is wrong with a source to correct it; the gap is that real river traffic met current,
  windings, shallows, portage and towpath obstruction, none of which the barge model has. The Edict
  ratio is reached with a 1 to 1.5 km/h current against the boat, so this is a model gap (river
  conditions), not a mode to scale.
- Not done: the money ratio (carrier capital, return legs, losses via `freight_money_per_tonne_km`)
  needs a Rome opening's prices and is not asserted.

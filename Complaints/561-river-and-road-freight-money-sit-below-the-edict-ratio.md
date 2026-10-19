# River and road freight money sit below the Edict ratio

**Status:** open

Split from 541. `sim/tests/test_freight_money_ratio.py` reads the money rate per tonne-km the route search
charges (`unopened_sim()._freight_mode_costs(imbalance)`) and holds wide bands. Two modes pass only near the
low edge of those bands:

- **River over sea** sits near the bottom of the river band, well below the Edict's figure. The river is still
  water: no current to work against upstream, no windings that lengthen the haul, no shallows or towing.
- **Road over sea** sits far below the Edict's land-by-wagon range at a flat grade.

Measure: `python3 -c "from sim.tests.harness import unopened_sim; c=unopened_sim()._freight_mode_costs(0.0); print({m: round(c[m]/c['sail'],1) for m in c})"`.

Why it matters (CLAUDE.md 4.2): the share of trade by sea, river and land, and so where towns and industry sit,
follows from these ratios. A river that is nearly as cheap as the sea and a road several times too cheap pull
inland trade and siting away from the coast.

What it would take: find which physical input is off (river current and sinuosity on river edges, towing
labour upstream; the wagon's load, pace, feed and team per tonne-km on a road), each from a source, rather than
scaling a mode. Then tighten the two lower bands in the test toward the Edict figures.

## Diagnosis (no change made)

- **Road.** The road mode is a two-ox cart whose payload is limited only by the team's sustained pull against
  rolling resistance, so it carries several tonnes; nothing limits it by axle, wheel or frame strength. Feed is
  most of its money per tonne-km. A structural payload field on the vehicle (applied in `max_cargo_mass_kg`)
  would move the ratio most; it needs a sourced physical cart payload (Raepsaet on Roman land transport, or a
  cart-load survey). The Theodosian Code's post-wagon limits are legal caps, not physical ones, and must not be
  used to tune. A cap also raises the dirt-track cart, so cart against pack must be re-checked.
- **River.** River edges carry no current or sinuosity; `routes_rates.rate(..., current_km_per_hour)` already takes
  a current but nothing supplies it. Closing needs per-edge current (and sinuosity, which lengthens the haul but
  not the per-tonne-km ratio) from a sourced river hydrology, the route builder passing it to the rate, and a
  direction-aware money rate (`_freight_mode_costs` has no direction; a balanced flow averages the legs).
- Measure as above; at the time of writing river and road over sea were unchanged from 541's figures.

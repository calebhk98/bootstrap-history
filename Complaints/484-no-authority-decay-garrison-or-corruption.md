# Authority does not decay with distance: no garrison reach, no unrest-versus-garrison control, no revenue leakage

**Status:** open

- The army is a national headcount (`record.army`, `sim/agents/government.py`); `army_wanted` is the
  civilisation's `standing_army` scaled by hazards (`sim/engine/agents_port_budget.py`). It has no
  location, so it cannot project control anywhere.
- Route search already gives the cost from any tile to any other (`sim/geography/routes_search.py`,
  `costs_from`, `reach`) and `territory.py` gives frontier and road length, but nothing reads them as
  authority.
- Revenue bases (`sim/agents/revenue_bases.py`) take no distance, control or loyalty input, and there is
  no corruption or leakage mechanism (`grep -rni "corrupt\|leakage" sim` finds save-file messages only).

Why it matters: the group's reports ask for control that falls with transport cost from the capital and
rises with transport technology, a control class that follows from garrison against unrest, and revenue
that leaks more in far, disloyal or badly held provinces. These are what make an overstretched empire
visible.

What it would take: garrisons located on tiles (485); an effective-control figure per tile from garrison
strength, route cost from the seat of government and local unrest (486); revenue assessment that takes
that figure, so leakage is an outcome. 483 (tile control) is closed.

**What 485 now gives this:** armies are located (`state.economy.campaigns["armies"]`, `Army.tile`), so a garrison on a tile is
a record to count: the soldiers of an owner standing on a tile, by tile. A taken tile enters at the `conquest` level of
`data/world/control_levels.json` and rises with the years an army stays on it (`campaign_year._consolidate_conquests`):
that rule is the first control level read from a garrison, and its step years are a heuristic that retires to this
complaint. Left for this one: control from garrison against unrest and route cost from the seat (`reach`), and revenue that
takes the figure.

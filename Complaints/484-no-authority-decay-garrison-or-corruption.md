# Authority does not decay with distance: no garrison reach, no unrest-versus-garrison control, no revenue leakage

**Status:** partly - reach, hold against a rising, collection, order and the levy reading authority, and corruption as the share officials keep are built; open: the remainders below

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

**Built (484 and 486 together, tests `sim/tests/test_stability_rules.py`, scenario `test_stability_scenario.py`):**
- Reach of a tile is the collection share (`sim/agents/collection.py`: officials, their time, roads from the seat); it falls with
  distance and rises with officials and roads. Hold is one minus the chance a rising of the tile's discontented beats the
  garrison on it (`sim/agents/authority.py` `hold`, over `battle.attacker_win_probability`; the garrison is the located
  army of 485 plus the share of free soldiers the tile's people bear). Authority is reach times hold; `CollectionView._held`
  (`collection_world.py`) applies it to collection and to order, and the labour and army levy reads it (`revenue_labour.levy_of`).
- Corruption is the share officials keep: `authority.share_kept`, rising with days of road from the seat and falling with the
  share of the people inspectors check; `CollectionView.corruption_share`; `revenue.leaked` takes it off every assessment
  (money, tonnes, payers).
- Heuristics added, each retiring here: `OFFICIAL_KEEP_CEILING`, `OFFICIAL_KEEP_DISTANCE_SCALE_DAYS`. No source opened gives a
  share kept by officials in a pre-modern state.

**Left:** the control level of a tile (`data/world/control_levels.json`) still rises by `conquest.steps` years, not by
authority; the share officials keep is not yet booked as the officials' income (it leaves the economy); conscription on a tile
is the levy scaled by the state-wide reach, not tile by tile (soldiers are raised from the state's force, not from a tile's
people); inspectors' own corruption and competence of the ruler do not feed the keep share.

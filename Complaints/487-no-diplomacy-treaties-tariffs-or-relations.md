# No diplomacy: no treaties, state-set tariffs, embargoes, trust, or notes on other powers; tolls ignore volume

**Status:** open

- A foreign state can shut its market to one smuggler (`sim/agents/government_foreign.py`) and has an
  export policy for its monopolies (`sim/agents/policy.py`). Nothing else: no treaty, tariff a state sets,
  embargo, quota, or trust score. `sim/engine/living_stock_smuggling.py` notes the diplomatic memory "the
  model does not yet have".
- Route dues are a flat per-mode labour-hour charge on a change of mode (`sim/geography/queries.py`,
  `dues_hours_per_tonne`), with no owner, no response to volume, and no competition between routes.
- Routes are open all year: no mud season, winter ice or monsoon in the route modes
  (`data/world/geography/route_modes/`; `sim/geography/freight_cost.py` cites a mud season as a source note only).
- A canal is a way built on a land edge between held tiles (`sim/engine/ways.py`,
  `sim/ui/proto/dispatch_ways.py`); a sea-to-sea canal (Nile to Red Sea, Suez, Panama, an invented one)
  needs a sea link in map data (`data/world/geography/sea_links/`, a catalogue a mod overlay can
  extend; not tested in this review), and no player action can build one.
- The `note` command keeps a seat's free text by year or attached to a project
  (`sim/ui/proto/dispatch_notes.py`); nothing keys a note to another country, and a note dies with its
  seat (481).

Why it matters: the group models toll revenue that shifts when a competing overland route opens, and
relations (their China and India split) that change what each power will do. Where a mechanism is not
yet reliable, they asked at least for a place to record a player's view of another power.

What it would take: a relations store keyed by pairs of actors (treaties with terms, tariff and embargo
settings, a free-text note); route dues owned by the tile owner (483) and set by policy; a buildable
sea-link canal as a way. A note store is the cheap first step.

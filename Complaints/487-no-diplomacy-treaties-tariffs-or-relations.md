# No diplomacy: no treaties, state-set tariffs, embargoes, trust, or notes on other powers; tolls ignore volume

**Status:** open - split into 597, 598, 599, 600, 601 (closes when they do)

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

## Staged plan (sized, no change made)

1. **Relations store and notes (small):** declare an actor-pair `relations` store in `data/world/stores.json`
   (treaty terms, tariff, embargo, trust, note); `relations` and `set_relation` commands where a seat sets only its
   own country's side (seat-to-country from `core_seats.py`, `agents_port_seats.py`); notes keyed to a country, not a
   seat, so they survive it (`dispatch_notes.py`; see 481).
2. **Tariff and embargo (medium to large):** the cross-border pricing point is `landed_price`
   (`sim/engine/goods_market_offers.py`); an embargo removes the offer, a tariff adds to the partner cost, revenue
   reaches the setting government through the ledger (`TaxForm` customs in `sim/economy/taxes.py` has one rate and no
   partner). Price caches must be invalidated when a relation changes mid-game.
3. **Owned route dues and seasonal closures (medium each, one session):** `dues_hours_per_tonne`
   (`sim/geography/queries.py`) has no tile; dues become a per-edge cost owned by the tile's owner in
   `routes_compile`/`routes_search` (consumers `foreign_routes._freight_handling_costs`, `domestic_haul`). The route
   search is date-free, so seasons need a design choice: an annualised cost or day multiplier per edge, or a
   season-aware search; the closures need sourced data in the route modes.
4. **Sea-link canal (medium):** `build_way` handles land edges only and sea links are a static catalogue; a canal
   needs a runtime overlay on the sea-link graph and a recompiled route graph, plus a way definition with costs.

## Split

Children, in order of work:

- 597 (closed): There is no relations store: no place to record a treaty, trust or a player's view of another power
- 598: States cannot set tariffs or embargoes: customs has one rate and no partner
- 599: Route dues are a flat per-mode charge with no owner, no response to volume and no competition between routes
- 600: Routes are open all year: no mud season, winter ice or monsoon in the route modes
- 601: No player action can build a sea-to-sea canal

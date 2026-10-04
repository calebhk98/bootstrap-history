# The trade registry drops fields labour needs, so trade facts are still written in code

**Status:** open

`sim/engine/catalog.py` `Trade` keeps only `family`, `training`, `training_years`, `note`,
`initially_absent` and `source`. `_trade_from` drops any other field a data file or mod states, and
`sim/engine/labour_port.py` gives labour no way to read the registry at all. So the labour package
cannot read:
- `difficulty`: how hard a trade is to finish (ability units, `sim/labour/market/aptitude.py`)
- `fallback`: the work anyone can take up at once
- `fatality_risk_per_year`
- `literate`: literacy caps how many there are
- `taught_from`: the default trade a new trade is taught from
- `tool_basket`: materials a worker replaces
- `staff_resource`

Each is held by hand in `sim/labour/legacy_trade_defaults.py`, the one labour module allowed to name
trades. Until then, a mod's new trade gets the generic answer (not literate, no tools, difficulty from
training years, the default teacher), and cannot say otherwise.

What it would take:
- `Trade` keeps unknown fields. One option is an `extra: Mapping` holding everything not named, merged by
  `deep_merge` as overrides already are.
- `LabourWorld` gains `trade_registry` (the merged mapping).
- `data/world/trades.json` states the fields, from the tables in `legacy_trade_defaults.py`.
- `sim/labour/trade_data.py` reads the registry first. The legacy tables and their `LEGACY_TRADE_TABLES`
  marker are then deleted.
- `difficulty` per trade is the important new datum. It is what keeps a hard trade's wage high while
  anyone may try it.

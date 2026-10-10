# Held living stock does not breed, die or spread, and a player has no command to buy it

**Status:** closed - held stock breeds and dies each year, is fed from the pasture or nursery land of its place and paid for in labour; `buy living_stock` buys it from a partner whose state sells it; `buy smuggled_stock` takes it from one that will not, at a risk; rubber, pepper, dairy cattle, tea, coffee and sugar cane have rows; the partner's refusal is its state's export policy

Living stock is now a held material (Complaints/365): `silkworm_eggs_kg`, `ramie_stock_kg`,
`draught_animal_kg` sit in the same ledger as any stock, and nodes name them in `holds`. As first reported, this was
missing (see What is done and What remains below):

- Held stock never changes by itself. A herd should calve and die, eggs should hatch or spoil, a
  planting should multiply; today the ledger entry is constant until sold or spent. Breeding and
  improving stock (growing worms, breeding animals) should be side branches with their own
  industry that raise the held amount, and a loss rule should lower it.
- The only purchase path is `Sim.buy_stock_from_partner` (`sim/engine/living_stock.py`); no
  command in the protocol calls it, so a player cannot buy eggs from a partner that sells them.
  Selling or emergency liquidation (`sim/engine/cash_remedies.py` sells any held material) can also
  sell living stock; breeding stock should be exempt or priced as breeding stock.
- Smuggling and theft (a stock taken from a partner that refuses to sell) have no mechanism, so
  a partner's refusal to sell (`data/civilizations/han_china_100ad.json`) left a society without
  a route to the stock except an expedition that grants it.
- The refusal is a civilisation data field read in `sim/engine/foreign_economies.py`; an actor-based
  export policy (`sim/agents/policy.py`) should replace it.

## What is done

- `buy living_stock <material> <units> [<partner>]` and `quote living_stock ...` (`sim/engine/living_stock_trade.py`,
  `sim/ui/proto/stock_purchases.py`): priced at the partner's price in home money plus the merchants' terms and
  the route's freight, paid through the goods market (`GoodsMarket.settle_import`), delivered into the held-stock
  ledger. The quote and the charge are one function, `Sim.stock_purchase_quote`; a row in
  `sim/tests/test_quote_matches_charge.py` pins it. A partner that will not sell refuses with its reason
  ("... will not sell ..."), and a partner sells no more than it started holding (a labelled transitional
  heuristic: partner stock is not simulated).
- Held stock breeds and dies each year (`sim/engine/living_stock_yearly.py`, `sim/world/stock_dynamics.py`, rates in
  `data/world/living_stock.json`): a holding at or above its breeding minimum grows by its natural increase, any
  holding falls by its loss, as expected values. Every rate is a labelled temporary heuristic with its reasoning in
  its `basis`; the original rows were not checked against a source, the five added for the folded crops carry `source` and
  `confidence` fields. The increase is not limited by feed or pasture.

## What was done to close it

- Smuggling (`sim/engine/living_stock_smuggling.py`, `buy smuggled_stock <material> <units> [<partner>]`, `quote` first): any actor
  that can reach a partner that holds the stock and will not sell it may take it. It pays the carrying (the agents at both ends
  and the freight over the route, not the price), loses what the route loses, and the partner's state catches it with the chance
  its reach gives times how much of its holding goes (the way a state catches an unlicensed operator of a patented concern,
  `sim/agents/enforcement.py`; `sim/world/stock_dynamics.py`). Caught, the stock is seized, the carrying is not refunded, the
  partner's government actor shuts its markets to the taker for years (`closed_markets` in its record, read by `partner_refusal`) and
  the taker's scandal rises; not caught, the stock arrives and the partner has less to sell (`stock_taken`). The draw is fixed by
  the attempt, so a save and load cannot change it. The years shut and the scandal are labelled temporary heuristics.
- A held herd has a place and draws on it (`sim/engine/living_stock_growth.py`): the held tile nearest the middle of the holder's
  tiles. A row with `grows_on` "pasture" gains no more than the live weight the tile's grass keeps beside what already grazes
  (`pasture_capacity_kg`, `sim/geography/food_pasture.py`); one with "arable" gains no more than the tile's arable land raises at the
  output per hectare of its production entry (`arable_hectares`). The labour of any gain is that entry's labour at the going wage,
  paid from the purse; a purse that cannot pay gets the share of the gain it can pay for. The ledger has one holder, so the place
  is the holder's seat; stock held by a concern on its own tile would need a ledger per concern. Two labelled simplifications: the
  grass a held herd eats is not taken from the herds that feed the people of the tile, and a herd above its pasture's capacity is not
  starved down, only stopped from growing.
- The plant rows' doubling cap is removed for sugar cane, whose multiplication is sourced as a mass ratio. It stays, labelled and with
  the reason, for pepper, tea and coffee: their sources give counts of cuttings or seeds per plant, and no source gives what a cutting
  weighs against its mother plant, so a count cannot yet become a ratio of kilograms.
- Rubber: `ag2_rubber_plantation` (planted rubber, budded-stump nurseries and tapping), its knowledge section in
  `docs/knowledge/76_farming_food_deep.md` (confidence C on the procedure, D on every number; sources named from memory, not opened),
  its nursery entry in `data/production/95_living_stock_crops.json`, and its row `rubber_planting_stock_kg`.
- Partner sales: a nursery entry with no node gate and a climate class (`tea_plant_stock_native_kg`, `sugar_cane_sett_native_kg`, as
  `cassia_kg` is made) lets a society whose territory is in the crop's climate make it from the start, so Han China, which lists the
  stock in its `opening_stock`, is priced for it and sells it. No civilisation in the data is in the climate of pepper, coffee or a
  dairy herd, so no partner offers those rows yet; a civilisation file that lists them and holds a native entry for them does so with
  no engine change.
- The refusal is the partner state's decision: `ExportPolicy` (`sim/agents/policy.py`) is the policy of every government actor, which
  starts with the monopolies its country's data lists (`state_monopolies`, replacing `will_not_sell`) in its record and keeps those
  back from sale abroad. `partner_refusal` asks the actor; before the roster is seeded it asks the same policy with the data.
- Tests: `sim/tests/test_stock_export_policy.py` (policy, actor record, feed room, catch chance) and
  `sim/tests/test_stock_growth_and_smuggling.py` (growth, feed, nursery land, labour and smuggling on a small stand-in for the game).

## Still true, not part of this complaint

- Pricing a breeding animal separately was dropped by the owner (2026-10-09): it sells like any good through `sell`.
- Held stock is not simulated at the partner: what a partner can sell is what it started with, less what smugglers took (a
  labelled transitional heuristic in `sim/engine/living_stock_trade.py`).

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 365 (`closed/365-living-stock-is-modelled-as-research.md`): living stock is modelled as research; pepper, rubber, dairy cattle, tea, coffee and sugar have no stock nodes.

Owner decision (2026-10-09): a breeding animal sells like any other good through `sell`, at the market's price; there is no separate breeding-stock price, so that item is dropped.

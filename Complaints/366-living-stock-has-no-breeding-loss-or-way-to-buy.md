# Held living stock does not breed, die or spread, and a player has no command to buy it

**Status:** partly - held stock breeds and dies each year and `buy living_stock` buys it from a partner; the cash-remedies list no longer offers living stock for sale; smuggling, theft, feed and pasture draw, stock nodes for the folded crops and an actor-based export policy remain

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
  a partner's `will_not_sell` (`data/civilizations/han_china_100ad.json`) leaves a society without
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
  its `basis`; none was checked against a source. The increase is not limited by feed or pasture.

## What remains

- Smuggling and theft have no mechanism: a stock taken from a partner that refuses to sell needs an agent that
  crosses the border, a chance of being caught, and the partner's response. Not attempted; it needs the partner as
  an actor.
- Breeding by labour (the production entries for the stock materials) is priced for a partner's sale but a held
  herd does not draw on pasture, labour or feed when it grows.
- The `sell` command still sells living stock when a player names it; only the cash-remedies list is exempt
  (`sim/tests/test_refusal_cash_remedies.py`). Pricing it as breeding stock is open.
- Feed and pasture: the pasture model (`sim/geography/food_pasture.py`) is per tile and a held herd has no tile, so a
  held herd cannot draw on it yet; the herd needs a place before it can eat.
- Stock nodes for pepper, rubber, dairy cattle, tea, coffee and sugar (folded 365): not added; each needs sourced
  propagation and loss facts for its `data/world/living_stock.json` row, and none was gathered.
- The partner's refusal is still a civilisation data field (`will_not_sell`); an actor-based export policy
  (`sim/agents/policy.py`) should replace it.

- Done: `cash_remedies` skips every material that has a row in `data/world/living_stock.json`.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 365 (`closed/365-living-stock-is-modelled-as-research.md`): living stock is modelled as research; pepper, rubber, dairy cattle, tea, coffee and sugar have no stock nodes.

# Held living stock does not breed, die or spread, and a player has no command to buy it

**Status:** open

Living stock is now a held material (Complaints/365): `silkworm_eggs_kg`, `ramie_stock_kg`,
`draught_animal_kg` sit in the same ledger as any stock, and nodes name them in `holds`. What is
still missing:

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
  export policy (`sim/engine/actors/policy.py`) should replace it.

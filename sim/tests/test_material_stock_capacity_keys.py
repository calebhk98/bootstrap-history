"""`settled_stock` (sim/ledger/rules.py): a capacity key (hours) written into the tonnes ledger is moved into the capacity
pool and leaves the stock, and the move is not redone on a read that wrote nothing."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.ledger.api import rules as ledger_rules

pool = {"scholar_hours": 1.0}
stock = ledger_rules.settled_stock(None, pool)
stock["scholar_hours"] += 5.0
stock["iron"] += 3.0
stock["patronage"] += 2.0
again = ledger_rules.settled_stock(stock, pool)
check("an hours key written to the stock lands in the pool added to what was there", pool["scholar_hours"] == 6.0, pool)
check("a non-physical key is moved too", pool.get("patronage") == 2.0, pool)
check("both leave the stock and a material stays", dict(again) == {"iron": 3.0}, dict(again))
check("the stock is the same ledger on every read", again is stock and isinstance(stock, ledger_rules.StockLedger))
again["scholar_hours"] += 1.0
ledger_rules.settled_stock(again, pool)
check("a later hours write is moved on the next read", pool["scholar_hours"] == 7.0, pool)

resumed_pool = {}
promoted = ledger_rules.settled_stock({"iron": 4.0, "smith_hours": 2.0}, resumed_pool)
check("a stock a save hands back as a plain dict is promoted and swept",
      isinstance(promoted, ledger_rules.StockLedger) and dict(promoted) == {"iron": 4.0} and resumed_pool["smith_hours"] == 2.0,
      (promoted, resumed_pool))

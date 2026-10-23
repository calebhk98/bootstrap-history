"""MaterialSupplyMixin._material_stock on a stand-in self: a capacity key (hours) written into the stock is moved into the
capacity pool and leaves the stock, and the move is not redone on a read that wrote nothing."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine.economy_materials import MaterialSupplyMixin, _StockLedger


def stand_in():
    return SimpleNamespace(state=SimpleNamespace(economy=SimpleNamespace(capacity_pool={"scholar_hours": 1.0}),
                                                 holdings=SimpleNamespace(_material_stock_ledger=None)),
                           NON_PHYSICAL_CAPACITY_KEYS=frozenset({"patronage"}))


world = stand_in()
stock = MaterialSupplyMixin._material_stock(world)
stock["scholar_hours"] += 5.0
stock["iron"] += 3.0
stock["patronage"] += 2.0
again = MaterialSupplyMixin._material_stock(world)
pool = world.state.economy.capacity_pool
check("an hours key written to the stock lands in the pool added to what was there", pool["scholar_hours"] == 6.0, pool)
check("a non-physical key is moved too", pool.get("patronage") == 2.0, pool)
check("both leave the stock and a material stays", dict(again) == {"iron": 3.0}, dict(again))
check("the stock is the same ledger on every read", again is stock and isinstance(stock, _StockLedger))
again["scholar_hours"] += 1.0
MaterialSupplyMixin._material_stock(world)
check("a later hours write is moved on the next read", pool["scholar_hours"] == 7.0, pool)

resumed = stand_in()
resumed.state.holdings._material_stock_ledger = {"iron": 4.0, "smith_hours": 2.0}
promoted = MaterialSupplyMixin._material_stock(resumed)
check("a stock a save hands back as a plain dict is promoted and swept",
      isinstance(promoted, _StockLedger) and dict(promoted) == {"iron": 4.0} and resumed.state.economy.capacity_pool["smith_hours"] == 2.0,
      (promoted, resumed.state.economy.capacity_pool))

"""The living-stock module: herds held in the ledger, needed by nodes, granted, bred, bought and smuggled.

A node's `holds` ({material: units}) is a start gate beside `pre`: the stock must be in the ledger now, however it came
there. A civilisation's `opening_stock` is what it held at its date; a node's `grants` is the stock a completed venture
brings back; a partner that makes the material and does not refuse sells it, and held stock breeds and dies by the rates
in data/world/living_stock.json. Which materials are stock is data; nothing here names one."""
from sim.assembly.api import Module

from .holding import Holding
from .trading import Trading
from .yearly import Yearly


class LivingStock(Holding, Yearly, Trading, Module):
    pass

"""The foreign-trade module: the partner countries as economies and the founder's, and every actor's, trade with them.

Each enabled partner has the facts of its own society (its prices in home money, the route to it, what it can make and wants),
a book per commodity that clears with the traders' cargo each year, and a ledger of the goods and coin that crossed and the
lift its route's carriers gave. Goods are paid for in coin metal; the traders' cargo is kept as legs until the home market has
cleared and settled once. Money moves through the ledger module's commands, the carriers and merchants' terms are freight's."""
from sim.assembly.api import Module

from .actor_trade import ActorTrade
from .capacity import Capacity
from .cargo import Cargo
from .economies import Economies
from .governments import Governments
from .payments import Payments
from .quotes import Quotes


class ForeignTrade(Cargo, ActorTrade, Quotes, Payments, Capacity, Governments, Economies, Module):
    def setup(self):
        self._partner_civs = {}          # the civilisation files loaded so far (never saved)
        self._facts_cache = {}           # acting seat -> partner -> (prices, facts, techniques known, coin price)
        self._materials_cache = {}       # acting seat -> (household prices, commodity -> material keys)
        self._can_make_cache = {}        # (partner, material) -> whether its techniques and regions supply it
        self._demand_cache = {}          # partner -> {commodity: (tonnes wanted, tonnes it can make)}

"""The foreign-trade module: the partner countries as economies and the founder's, and every actor's, trade with them.

Each enabled partner is a country of the one agent economy, which owns its prices and quantities. Here it has the facts of
its civilisation file (the route to it), and a ledger of the goods and coin that crossed and the lift its route's carriers gave. Goods are paid for in coin metal; the traders' cargo is kept as legs until the home market has
cleared and settled once. Money moves through the ledger module's commands, the carriers and merchants' terms are freight's."""
from sim.assembly.api import Module

from .actor_trade import ActorTrade
from .cargo import Cargo
from .economies import Economies
from .governments import Governments
from .payments import Payments
from .quotes import Quotes


class ForeignTrade(Cargo, ActorTrade, Quotes, Payments, Governments, Economies, Module):
    def setup(self):
        self._partner_civs = {}          # the civilisation files loaded so far (never saved)
        self._facts_cache = {}           # acting seat -> partner -> (prices, facts, techniques known, coin price)
        self._materials_cache = {}       # acting seat -> (household prices, commodity -> material keys)

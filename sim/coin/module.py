"""The coin module: coin as a metal. It owns the recorded value of each coin metal and the society's price level; it
keeps, carries and loses coin by the commands in commands.py and the surcharge it answers the ledger with."""
from sim.assembly.api import Module

from .carriage import Carriage
from .keeping import Keeping
from .prices import Prices
from .theft import Theft


class Coin(Module):

    PARTS = {
        "prices": Prices,
        "keeping": Keeping,
        "carriage": Carriage,
        "theft": Theft,
    }

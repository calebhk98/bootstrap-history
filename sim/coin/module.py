"""The coin module: coin as a metal. It owns the recorded value of each coin metal and the society's price level; it
keeps, carries and loses coin by the commands in commands.py and the surcharge it answers the ledger with."""
from sim.assembly.api import Module

from .carriage import Carriage
from .keeping import Keeping
from .prices import Prices
from .theft import Theft


class Coin(Prices, Keeping, Carriage, Theft, Module):
    def setup(self):
        self._home_opening = None        # coin the society opened with, worked out on first use (never saved)
        self._partner_openings = {}

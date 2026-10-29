"""The actors module: the cast of governments, firms, traders and bodies of people beside the founder's households, their saved
records and registry, and the world the agents package asks its questions of.

The records live in the module's world slot (`ActorsState`, sim/agents/records.py). The module hands the registry out as the
view `cast` and runs the actors' year when it is sent `AdvanceActors`; what the actors ask of the economy, the labour market,
the land and the seats it reads through the views its spec declares."""
from sim.assembly.api import Module

from .cast import Cast
from .contact import Contact
from .cause_views import CauseViews
from .country_views import CountryViews
from .lending import Lending
from .literacy_views import LiteracyViews
from .seat_exchange import SeatExchange
from .seat_parties import SeatParties
from .staff import Staff
from .year import Year


class Actors(Cast, CountryViews, LiteracyViews, CauseViews, Lending, SeatParties, SeatExchange, Staff, Contact, Year, Module):

	def setup(self) -> None:
		self._registry = None   # never saved: rebuilt over the world slot on first use and after a load
		self._extensions = None   # never saved: asked of the providers on first use

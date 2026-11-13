"""The actors module: the cast of governments, firms, traders and bodies of people beside the founder's households, their saved
records and registry, and the world the agents package asks its questions of.

The records live in the module's world slot (`ActorsState`, sim/agents/records.py). The module hands the registry out as the
view `cast` and runs the actors' year when it is sent `AdvanceActors`; what the actors ask of the economy, the labour market,
the land and the seats it reads through the views its spec declares."""
from sim.assembly.api import Module

from .actor_sheets import ActorSheets
from .cast import Cast
from .cause_views import CauseViews
from .contact import Contact
from .country_views import CountryViews
from .lending import Lending
from .literacy_views import LiteracyViews
from .seat_exchange import SeatExchange
from .seat_parties import SeatParties
from .society import Society
from .staff import Staff
from .year import Year


class Actors(Module):

	PARTS = {
		"cast": Cast,
		"actor_sheets": ActorSheets,
		"society": Society,
		"country_views": CountryViews,
		"literacy_views": LiteracyViews,
		"cause_views": CauseViews,
		"lending": Lending,
		"seat_parties": SeatParties,
		"seat_exchange": SeatExchange,
		"staff": Staff,
		"contact": Contact,
		"year": Year,
	}

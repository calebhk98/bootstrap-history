"""What an actor can see and price: a read-only view of the simulated world.

Actors never touch the game directly. They ask this view, which answers from the views the actors module reads, which
keeps them free of the engine and lets a test or a second scenario supply another one.

`ActorWorld` holds no rule and no answer of its own: it is the set of parts that make up the view, one per concern, each
owning its own state and built here with the world it reads (`world.needs` and the actors module's `cast`, `seat_book` and
`staff` parts, `world.registry`) and reaching its siblings through it. Callers address the part: `world.<part>.<method>()`. The parts a world has are the
members of `sim/agents/protocols.py` `World`; a country's world (sim/agents/country_view.py) has the same parts.

    setting       the year, the tree, the civilisation, edges, random streams, the home government        (world_setting.py)
    knowledge     what the society knows and how far an onlooker sees an invention                          (world_knowledge.py)
    disclosure    how each invention was disclosed, patents and royalties                                  (world_disclosure.py)
    seats         the seats' staff and margins, the founder's business review                              (world_seats.py)
    people        population, literacy, the cost of a body of people to keep                               (world_people.py)
    army          the force the state wants and keeps, a soldier's equipment, the fleet                      (world_army.py)
    taxpayers     who the state can see and how far its officials reach                                     (world_taxpayers.py)
    revenue       the state's declared forms and the bases they read                                        (world_revenue.py)
    collection    the share of what is due that the state's officials collect, tile by tile                (world_collection.py)
    labour        the one labour market, what a trade pays, the people free to hire                          (world_labour.py)
    quotes        what the goods market quotes                                                              (world_quotes.py)
    groups        who is hurt and what an interest group can say                                            (world_groups.py)
    stakes        the stakes of the unemployed, the church, the academy and the landlords                  (world_stakes.py)
    patronage     what a state funds its own clients with                                                   (world_patronage.py)
    credit        the loanable-funds market and saving                                                      (world_credit.py)
    capacity      what it is worth to run a concern at a larger size                                        (world_capacity.py)
    site          the land a concern occupies and its rent                                                  (world_site.py)
    concerns      a concern's crew, cost, takings, margin and ramp                                          (world_concerns.py)
    enterprises   the figures a state's plants are booked from                                              (world_enterprises.py)
    market        offering and bidding at the one goods market                                              (world_market.py)
    trade         places with a market, prices, freight and cargo                                           (world_trade.py)
    research      hands, sellers and substitutes for a research start                                       (world_research.py)
"""
from typing import Any

from .world_army import Army
from .world_capacity import Capacity
from .world_credit import Credit
from .world_collection import HomeCollection
from .world_concerns import Concerns
from .world_disclosure import Disclosure
from .world_enterprises import Enterprises
from .world_groups import Groups
from .world_knowledge import Knowledge
from .world_labour import ActorLabourReads
from .world_market import Market
from .world_patronage import Patronage
from .world_people import People
from .world_quotes import Quotes
from .world_research import Research
from .world_revenue import Revenue
from .world_seats import Seats
from .world_setting import Setting
from .world_site import Site
from .world_stakes import Stakes
from .world_taxpayers import Taxpayers
from .world_trade import Trade


class ActorWorld:
	"""The parts of the view of one simulation's actors. `needs` is what the actors module reads; `cast`, `seat_book` and
	`staff` are the actors module's parts that keep the registry, the seats' parties and the staff of the actors."""

	def __init__(self, needs: Any, cast: Any = None, seat_book: Any = None, staff: Any = None) -> None:
		self.needs = needs
		self.cast = cast
		self.seat_book = seat_book
		self.staff = staff
		self.setting = Setting(self)
		self.knowledge = Knowledge(self)
		self.disclosure = Disclosure(self)
		self.seats = Seats(self)
		self.people = People(self)
		self.army = Army(self)
		self.taxpayers = Taxpayers(self)
		self.revenue = Revenue(self)
		self.collection = HomeCollection(self)
		self.labour = ActorLabourReads(self)
		self.quotes = Quotes(self)
		self.groups = Groups(self)
		self.stakes = Stakes(self)
		self.patronage = Patronage(self)
		self.credit = Credit(self)
		self.capacity = Capacity(self)
		self.site = Site(self)
		self.concerns = Concerns(self)
		self.enterprises = Enterprises(self)
		self.market = Market(self)
		self.trade = Trade(self)
		self.research = Research(self)

	@property
	def registry(self) -> Any:
		"""The cast of actors the module keeps."""
		return self.cast.cast()

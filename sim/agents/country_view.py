"""`CountryWorld`: the world an actor of another country sees.

It has the parts of the shared world (`ActorWorld`, sim/actors/world.py). Questions about the country (its people,
state and its revenue, techniques, values, government, how much of the founder's work reaches it) are answered by
parts built here from its profile, and its pay, output and prices from its own part of the economy. Every other part is
the shared world's, passed straight through (`SharedPart`, its members installed from the part's protocol).

    setting, knowledge             country_setting.py       people                 country_people.py
    labour, research               country_labour.py        revenue, army, taxpayers   country_revenue.py, country_army.py,
    collection, credit, quotes,   country_money.py                                country_taxpayers.py
    market                                                  groups, stakes         country_groups.py
    patronage                      country_patronage.py     concerns, site         country_state_site.py
    enterprises                    country_state_books.py
"""
from typing import Any

from .country_army import CountryArmy
from .country_groups import CountryGroups, CountryStakes
from .country_labour import CountryLabour
from .country_money import CountryCredit, CountryCollection, CountryMarket, CountryQuotes
from .country_part import OwnEconomy, SharedCapacity, SharedDisclosure, SharedSeats, SharedTrade
from .country_patronage import CountryPatronage
from .country_people import CountryPeople
from .country_revenue import CountryRevenue
from .country_setting import CountryKnowledge, CountrySetting
from .country_state_books import CountryEnterprises
from .country_state_crew import CountryResearch
from .country_state_site import CountryConcerns, CountrySite
from .country_taxpayers import CountryTaxpayers
from .no_country_economy import NoCountryEconomy  # noqa: F401  (raised by the parts; callers import it from here)
from .records import CountryProfile


class CountryWorld:
	"""What an actor of `profile`'s country sees. `shared` is the shared world, `holder` the registry."""

	def __init__(self, shared: Any, profile: CountryProfile, holder: Any) -> None:
		self.shared = shared
		self.profile = profile
		self.holder = holder
		self.own = OwnEconomy(shared, profile)
		self.setting = CountrySetting(self)
		self.knowledge = CountryKnowledge(self)
		self.disclosure = SharedDisclosure(self)
		self.seats = SharedSeats(self)
		self.people = CountryPeople(self)
		self.army = CountryArmy(self)
		self.taxpayers = CountryTaxpayers(self)
		self.revenue = CountryRevenue(self)
		self.collection = CountryCollection(self)
		self.labour = CountryLabour(self)
		self.quotes = CountryQuotes(self)
		self.groups = CountryGroups(self)
		self.stakes = CountryStakes(self)
		self.patronage = CountryPatronage(self)
		self.credit = CountryCredit(self)
		self.capacity = SharedCapacity(self)
		self.site = CountrySite(self)
		self.concerns = CountryConcerns(self)
		self.enterprises = CountryEnterprises(self)
		self.market = CountryMarket(self)
		self.trade = SharedTrade(self)
		self.research = CountryResearch(self)

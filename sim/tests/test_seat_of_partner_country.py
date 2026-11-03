"""A seat that belongs to a partner country deals in that country's own markets and answers to its government:
the same question gives a different, correct answer for a home seat and a partner seat (stand-ins
two-country economy and stand-ins, no game)."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.actors.module import Actors
from sim.markets import reads_prices
from sim.markets.reads_prices import PriceReads
from sim.markets.year_figures import YearFigures
from sim.seats.module import Seats
from sim.seats.state import SeatsSeat
from . import module_harness

COIN_PER_UNIT = 2.0
HOME, NORTH = "home", "north"
LABOURER = "labourer"
# what the economy's own readers return for a market scope: the home country's, then the north's
WAGES = {None: {LABOURER: 10.0}, NORTH: {LABOURER: 15.0}}
PRICES = {None: {"grain": 3.0}, NORTH: {"grain": 5.0, "salt": 7.0}}


class Stored(dict):
    pass


STORED = Stored(on=True)


class FakeSim:
    scenario = SimpleNamespace(civ={"id": HOME})

    def agent_record(self):
        return STORED


def seat_economy():
    """`PriceReads` over a stand-in economy whose figures `answers` reads through the economy's readers."""
    economy = SimpleNamespace(setup=SimpleNamespace(coin_per_unit=COIN_PER_UNIT, countries=lambda: [HOME, NORTH],
                                                    unskilled_trade=LABOURER, civ_id=HOME))
    core = SimpleNamespace(figures=YearFigures(), economy=lambda: economy, current=lambda: True, stored=STORED)
    return PriceReads(core, FakeSim())


def answers_over_readers(call):
    """`call(agent)` with the economy's readers replaced by the figures above."""
    readers = {"country_trade_wage": lambda economy, trade, country=None: WAGES[country][trade],
               "shown_prices_of": lambda economy, country=None: (PRICES[country], set()),
               "interest_rate": lambda economy: 0.05}
    with mock.patch.multiple(reads_prices.economy_api, **readers):
        return call(seat_economy())


home_wage = answers_over_readers(lambda agent: agent.wage_per_hour(LABOURER))
north_wage = answers_over_readers(lambda agent: agent.wage_per_hour(LABOURER, NORTH))
check("a home seat is paid the home labour markets' wage", home_wage == WAGES[None][LABOURER] * COIN_PER_UNIT, home_wage)
check("a partner country's seat is paid that country's own wage, in the same coin",
      north_wage == WAGES[NORTH][LABOURER] * COIN_PER_UNIT, (home_wage, north_wage))
home_prices = answers_over_readers(lambda agent: agent.answers()[0])
north_prices = answers_over_readers(lambda agent: agent.answers(NORTH)[0])
check("a partner country's seat buys at the prices of the markets its tiles trade in",
      north_prices == {good: price * COIN_PER_UNIT for good, price in PRICES[NORTH].items()}, north_prices)
check("the home answers are the home markets' prices", home_prices == {"grain": 3.0 * COIN_PER_UNIT}, home_prices)


def after_naming_the_north(agent):
    agent.answers(NORTH)
    return agent.wage_per_hour(LABOURER)


check("the home answers are not moved by the other country's wages",
      answers_over_readers(after_naming_the_north) == home_wage, None)


def elsewhere(agent):
    return agent.answers("elsewhere") is agent.answers() and agent.wage_per_hour(LABOURER, "elsewhere") == agent.wage_per_hour(LABOURER)


check("a country the economy does not hold is answered as the home country", answers_over_readers(elsewhere), None)
check("the home answer is the same whether or not the country is named",
      answers_over_readers(lambda agent: agent.answers(HOME) is agent.answers()), None)


def seats_module(country):
    """The seats module over a one-seat registry whose seat plays for `country` (None is the game's own)."""
    module = module_harness.build(Seats, seat=SeatsSeat(country=country), views={"registered_seats": ["second"], "civilisation": {"id": "home"}})
    module.seat_slot_of = lambda seat_id: module.seat
    module.clock.act_as("second")
    return module


check("a seat of the game's own country has no partner country", seats_module(None).acting_country() is None
      and seats_module("home").acting_country() is None, None)
check("a seat of another country names it", seats_module("han").acting_country() == "han", None)


class Registry:
    def __init__(self):
        self.asked = []
        self.countries = self   # the registry's country part answers the government questions

    def government_of(self, country):
        self.asked.append(country)
        return "the partner's government" if country == "han" else None

    def ensure_government(self, country, name):
        return "the home government"


def Treasury(country):
    """The actors module over a stand-in cast, acting for a seat of `country`."""
    module = module_harness.build(Actors, views={"acting_country": lambda: country, "civilisation": {"id": "home", "name": "Home"}})
    registry = Registry()
    module.cast = lambda: registry
    module.seed_opening_cast = lambda: []
    return module
# not text: a stub treasury's descriptor
check("a partner country's seat pays the state of its own country", Treasury("han").state_treasury() == "the partner's government", None)
# not text: a stub treasury's descriptor
check("a home seat pays the home state", Treasury(None).state_treasury() == "the home government", None)
# not text: a stub treasury's descriptor
check("a partner country with no government of its own in the cast falls back to the home state",
      Treasury("norse").state_treasury() == "the home government", None)

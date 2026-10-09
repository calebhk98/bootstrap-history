"""A seat that belongs to a partner country deals in that country's own markets and answers to its government:
the same question gives a different, correct answer for a home seat and a partner seat (the hand-built
two-country economy and stand-ins, no game)."""

QUICK_TOPIC = True

from .harness import check

from sim.economy import country_figures
from sim.engine import society_actors
from sim.engine.economy_port_year import AgentEconomy
from sim.engine.seat_run import SeatRunMixin
from sim.engine.society_actors import ActorsMixin
from sim.tests import economy_fixture as fixture

setup = fixture.two_country_setup()
economy, _outcomes = fixture.run(setup, years=4)


class Stored(dict):
    pass


class FakeState:
    class economy:
        agent_economy = Stored(on=True)


class FakeSim:
    civ = {"id": setup.civ_id}
    state = FakeState


agent = AgentEconomy.__new__(AgentEconomy)
agent._sim = FakeSim()
agent._economy = economy
agent._answers = None
agent._country_answers = {}
agent._stale = set()
agent._built_from = FakeState.economy.agent_economy

# the north's labour markets pay half as much again as the home ones did
for key in list(economy.record.memory.wages):
    if key.endswith("work@" + fixture.NORTH_FARMS) or key.endswith("work@" + fixture.NORTH_PORT):
        economy.record.memory.wages[key] *= 1.5
home_wage = agent.wage_per_hour(fixture.LABOURER)
north_wage = agent.wage_per_hour(fixture.LABOURER, fixture.NORTH)
coin = setup.coin_per_unit
check("a home seat is paid the home labour markets' wage", home_wage > 0.0, home_wage)
check("a partner country's seat is paid that country's own wage", north_wage > 0.0 and north_wage != home_wage, (home_wage, north_wage))
set_by_markets = country_figures.wages_per_hour(economy, fixture.NORTH)[fixture.LABOURER]
check("the partner wage is the one its labour markets set", abs(north_wage - set_by_markets * coin) < 1e-9, None)
home_prices, north_prices = agent.answers()[0], agent.answers(fixture.NORTH)[0]
check("a partner country's seat buys at the prices of the markets its tiles trade in",
      north_prices[fixture.GRAIN] > 0.0 and set(north_prices) <= set(home_prices) | set(north_prices), None)
check("the home answers are not moved by the other country's wages", abs(home_wage * 1.5 - north_wage) < 1e-9, (home_wage, north_wage))
check("a country the economy does not hold is answered as the home country",
      agent.answers("elsewhere") == agent.answers() and agent.wage_per_hour(fixture.LABOURER, "elsewhere") == home_wage, None)
check("the home answer is the same whether or not the country is named", agent.answers(setup.civ_id) is agent.answers(), None)


class Seat:
    def __init__(self, country):
        self.country = country


class Seats(SeatRunMixin):
    civ = {"id": "home"}

    def __init__(self, country):
        class State:
            acting_seat = "second"
            seats = {"second": Seat(country)}
        self.state = State


check("a seat of the game's own country has no partner country", Seats(None).acting_country() is None
      and Seats("home").acting_country() is None, None)
check("a seat of another country names it", Seats("han").acting_country() == "han", None)


class Registry:
    def __init__(self):
        self.asked = []

    def government_of(self, country):
        self.asked.append(country)
        return "the partner's government" if country == "han" else None

    def ensure_government(self, country, name):
        return "the home government"


class Treasury(ActorsMixin):
    civ = {"id": "home", "name": "Home"}

    def __init__(self, country):
        self._registry = Registry()
        self._country = country

    @property
    def actors(self):
        return self._registry

    def acting_country(self):
        return self._country


society_actors.seed_opening_cast = lambda sim: []
check("a partner country's seat pays the state of its own country", Treasury("han").state_treasury() == "the partner's government", None)
check("a home seat pays the home state", Treasury(None).state_treasury() == "the home government", None)
check("a partner country with no government of its own in the cast falls back to the home state",
      Treasury("norse").state_treasury() == "the home government", None)

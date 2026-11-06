"""The parts of the port over the agent economy, built together and held by reference. Part of the port.

    agent        the live economy and the record it is rebuilt from (agent_economy.py)
    prices       prices, wages, the rate and the markets' books (reads_prices.py)
    households   cohorts, rents, need floors, partner countries, volumes (reads_households.py)
    producers    producers, capacity and the people who work (reads_producers.py)
    seats        each seat's concerns selling in the market (port_seat_concerns.py)
    trade        firms', states' and traders' sales and purchases (port_actor_trade.py)
    year         the year's run (port_year.py)
"""
from .agent_economy import AgentEconomy
from .port_actor_trade import ActorTrade
from .port_seat_concerns import SeatConcerns
from .port_year import YearRun
from .port_year_inputs import YearInputsBuilder
from .reads_households import HouseholdReads
from .reads_prices import PriceReads
from .reads_producers import ProducerReads


class AgentParts:

    def __init__(self, world):
        self.agent = AgentEconomy(world)
        self.prices = PriceReads(self.agent, world)
        self.households = HouseholdReads(self.agent)
        self.producers = ProducerReads(self.agent)
        self.seats = SeatConcerns(world, self.agent)
        self.trade = ActorTrade(world, self.agent, self.seats)
        self.year = YearRun(world, self.agent, self.seats, self.trade, YearInputsBuilder(world, self.agent, self.seats))

    def rename_agent(self, old, new):
        """A seat handed over: the economy's records and the year's notes carry the new name."""
        self.agent.rename_agent(old, new)
        self.trade.forget_index()

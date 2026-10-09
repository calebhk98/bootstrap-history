"""A seat holds patents and company shares like any actor: they live in its holdings, write through the party an
exchange deals with, pay dividends to it, and survive a save (small fixture, no game)."""
import json

from .harness import *  # noqa: F401,F403
from sim.agents import joint_stock, patent
from sim.agents.api import Household, HouseholdParty
from sim.agents.records import ActorRecord
from sim.engine.agents_port_household import HouseholdPort
from sim.engine.state import (FounderState, HouseholdState, ProjectsState, SimulationState, deserialize_state,
                              serialize_state)
from sim.engine.state_seat import FIRST_SEAT_ID, SeatState

QUICK_TOPIC = True

facade = Household(starting_capital=100.0, port=HouseholdPort())
state = facade._state
entered = []


class Switch:
    def __init__(self, seat_id):
        self.seat_id = seat_id

    def __enter__(self):
        entered.append(self.seat_id)

    def __exit__(self, *exc):
        return False


party = HouseholdParty(facade, seat_id=FIRST_SEAT_ID, act_as=Switch)
seat = state.seats[FIRST_SEAT_ID]
check("the party is named by the seat id", party.actor_id == FIRST_SEAT_ID, party.actor_id)
check("its patents and shares are the seat's own dictionaries",
      party.record.patents is seat.holdings.patents and party.record.holdings is seat.holdings.shares_held, None)


class Target:
    """Another actor: an id and a record."""
    actor_id = "firm:1"

    def __init__(self):
        self.record = ActorRecord(kind="firm")


target = Target()
party.record.patents["lathe"] = {"granted": 10, "expires": 30, "licensees": []}
patent.hand_over(party, target, {"licence": ["lathe"]})
check("a licence granted by the seat is written on the seat's holdings",
      seat.holdings.patents["lathe"]["licensees"] == ["firm:1"], seat.holdings.patents)
check("the live patent is found among the seat and other actors",
      patent.entry_among([target, party], "lathe", 20)["holder"] == FIRST_SEAT_ID, None)
patent.hand_over(party, target, {"patent": ["lathe"]})
check("selling the patent moves it off the seat", "lathe" not in seat.holdings.patents and "lathe" in target.record.patents, None)

target.record.holdings["firm:2"] = 0.4
joint_stock.hand_over(target, party, {"firm:2": 0.25})
check("shares bought by the seat are held on the seat", abs(seat.holdings.shares_held["firm:2"] - 0.25) < 1e-9, seat.holdings.shares_held)
party.record.issued = 0.2
check("issued equity writes through to the seat", seat.holdings.shares_issued == 0.2, seat.holdings.shares_issued)


class Issuer:
    actor_id = "firm:2"

    def __init__(self):
        self.record = ActorRecord(kind="firm", last_margin=100.0, issued=0.5)
        self.money = 1000.0
        self.paid = 0.0

    def debit(self, amount, purpose):
        self.money -= amount

    def credit(self, amount, purpose):
        self.money += amount


class Registry:
    def __init__(self, actors):
        self.actors = actors


class World:
    def seat_parties(self):
        return {FIRST_SEAT_ID: party}


issuer = Issuer()
before = facade.money
paid = joint_stock.pay_dividends(Registry({"firm:2": issuer}), World())
check("a firm pays its dividend to the seat that holds its shares", paid > 0.0 and abs(facade.money - before - paid) < 1e-6
      and entered, (paid, before, facade.money))

state.seats["second"] = SeatState(household=HouseholdState(capital=5.0), projects=ProjectsState(), founder=FounderState())
seat.holdings.patents["lathe"] = {"granted": 10, "expires": 30, "licensees": []}
loaded = deserialize_state(json.loads(json.dumps(serialize_state(state))), SimulationState)
check("patents, shares held and equity issued round-trip in the seat's holdings",
      loaded.seats[FIRST_SEAT_ID].holdings.patents["lathe"]["expires"] == 30
      and loaded.seats[FIRST_SEAT_ID].holdings.shares_held == {"firm:2": 0.25}
      and loaded.seats[FIRST_SEAT_ID].holdings.shares_issued == 0.2
      and loaded.seats["second"].holdings.patents == {}, None)

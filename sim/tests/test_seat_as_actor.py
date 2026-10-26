"""A seat holds patents and company shares like any actor: they live in the seat's stored dealings, write through the party an
exchange deals with, pay dividends to it, and survive a save (small fixture, no game)."""
import json

from .harness import *  # noqa: F401,F403
from sim.agents import joint_stock, patent
from sim.agents.api import Household, HouseholdParty
from sim.seats.api import SeatsSeat
from sim.agents.records import ActorRecord
from sim.engine.agents_port_household import HouseholdPort
from sim.engine.state import serialize_state
from sim.engine.state_seat import FIRST_SEAT_ID

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


seat = state.seats[FIRST_SEAT_ID]
slot = SeatsSeat()
party = HouseholdParty(facade, seat_id=FIRST_SEAT_ID, act_as=Switch, dealings=slot)
check("the party is named by the seat id", party.actor_id == FIRST_SEAT_ID, party.actor_id)
check("its patents and shares are the seat's own dictionaries",
      party.record.patents is slot.patents and party.record.holdings is slot.shares_held, None)


class Target:
    """Another actor: an id and a record."""
    actor_id = "firm:1"

    def __init__(self):
        self.record = ActorRecord(kind="firm")


target = Target()
party.record.patents["lathe"] = {"granted": 10, "expires": 30, "licensees": []}
patent.hand_over(party, target, {"licence": ["lathe"]})
check("a licence granted by the seat is written on the seat's holdings",
      slot.patents["lathe"]["licensees"] == ["firm:1"], slot.patents)
check("the live patent is found among the seat and other actors",
      patent.entry_among([target, party], "lathe", 20)["holder"] == FIRST_SEAT_ID, None)
patent.hand_over(party, target, {"patent": ["lathe"]})
check("selling the patent moves it off the seat", "lathe" not in slot.patents and "lathe" in target.record.patents, None)

target.record.holdings["firm:2"] = 0.4
joint_stock.hand_over(target, party, {"firm:2": 0.25})
check("shares bought by the seat are held on the seat", abs(slot.shares_held["firm:2"] - 0.25) < 1e-9, slot.shares_held)
party.record.issued = 0.2
check("issued equity writes through to the seat", slot.shares_issued == 0.2, slot.shares_issued)


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

class Shareholder:
    actor_id = "firm:7"

    def __init__(self):
        self.record = ActorRecord(kind="firm", holdings={FIRST_SEAT_ID: 0.2})
        self.money = 0.0

    def credit(self, amount, purpose):
        self.money += amount

    def debit(self, amount, purpose):
        self.money -= amount


class MarginWorld(World):
    def seat_margin(self, seat_id):
        return 400.0


# a seat that issued equity pays its shareholders a part of its margin
holder = Shareholder()
facade.capital = 1000.0
before = facade.money
paid = joint_stock.pay_dividends(Registry({"firm:7": holder}), MarginWorld())
check("a seat that issued equity pays its shareholder by share of its margin", paid > 0.0 and abs(holder.money - paid) < 1e-9
      and abs(before - facade.money - paid) < 1e-6, (paid, holder.money, before, facade.money))

state.seats[FIRST_SEAT_ID].modules["seats"] = slot
slot.patents["lathe"] = {"granted": 10, "expires": 30, "licensees": []}
saved = json.loads(json.dumps(serialize_state(state)))["seats"][FIRST_SEAT_ID]["modules"]["seats"]
check("patents, shares held and equity issued are saved with the seat's module state",
      saved["patents"]["lathe"]["expires"] == 30 and saved["shares_held"] == {"firm:2": 0.25} and saved["shares_issued"] == 0.2, saved)

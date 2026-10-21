"""SCENARIO (Complaint 640): Two named scenarios. A real game seeds its cast from the civilisation played and the economies trading with it, and the
whole cast takes its years with money conserved between actors."""
import random

from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorRecord, Player
from sim.engine.coin_hoard import KEEPING_CAUSE
from sim.engine.theft_charge import THEFT_CAUSE

GAME = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True,
             civ=S.load_civ("rome_100ad"))


def actor_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


actor_year(GAME)
registry = GAME.actors
state = registry.state
home = GAME.civ["id"]
partners = GAME.foreign_economies()
seeded = set(registry.actors)
before_cast = dict(state.cast)
cast_ok = (state.home_country == home and set(partners) <= set(state.countries) and home in state.countries
           and all(registry.get("government:" + partner).record.country == partner
                   and state.countries[partner].starting_techs == set(S.load_civ(partner)["starting_techs"])
                   for partner in partners))
actor_year(GAME)
check("scenario: a real game seeds its cast from the civilisation played and every economy trading with it, once",
      cast_ok and dict(state.cast) == before_cast and seeded <= set(registry.actors),
      (state.home_country, partners, list(state.countries)))

# a second player joins as data and plays through queued orders
second = registry.add("player:2", ActorRecord(kind="player", controller="llm", money=1000.0))
payee = registry.get("government:" + home)
received_before = payee.record.income.get("transfer", 0.0)
second.record.orders.append({"command": "transfer", "to": payee.actor_id, "amount": 250.0})
actor_year(GAME)
guards_paid = second.record.outlays.get(KEEPING_CAUSE, 0.0)
stolen = second.record.outlays.get(THEFT_CAUSE, 0.0)     # coin held unguarded is exposed to theft
check("scenario: a player's order in a real game moves coin from its purse to the other actor's, creating no money",
      isinstance(second, Player)
      and abs(second.money + guards_paid + stolen - 750.0) < 1e-9 and payee.record.income.get("transfer", 0.0) - received_before == 250.0
      and any(entry["command"] == "transfer" and entry["ok"] for entry in second.record.journal),
      (second.money, second.record.journal))

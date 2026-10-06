"""A real game seeds its cast from the civilisation played and the economies trading with it, and the
whole cast takes its years with money conserved between actors."""
import random

from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorRecord, Player
from sim.engine.coin_hoard import KEEPING_CAUSE

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
check("the home country is the civilisation played", state.home_country == home, state.home_country)
check("every economy trading with it is a country of the cast",
      set(partners) <= set(state.countries) and home in state.countries, (partners, list(state.countries)))
check("each foreign country has its own government with its own techniques",
      all(registry.get("government:" + partner).kind == "foreign_government"
          and state.countries[partner].starting_techs == set(S.load_civ(partner)["starting_techs"])
          for partner in partners))
check("the home country's people are bodies of people, not individuals",
      len([actor for actor in registry.actors.values() if actor.kind == "stratum" and actor.record.country is None]) >= 3)
seeded = set(registry.actors)
before_cast = dict(state.cast)
actor_year(GAME)
check("the cast is seeded once and kept", dict(state.cast) == before_cast and seeded <= set(registry.actors))

# a second player joins as data and plays through queued orders
second = registry.add("player:2", ActorRecord(kind="player", controller="llm", money=1000.0))
check("a second player is an actor of its own kind", isinstance(second, Player))
payee = registry.get("government:" + home)
received_before = payee.record.income.get("transfer", 0.0)
second.record.orders.append({"command": "transfer", "to": payee.actor_id, "amount": 250.0})
second.record.orders.append({"command": "no_such_command"})
actor_year(GAME)
guards_paid = second.record.outlays.get(KEEPING_CAUSE, 0.0)
check("a player's transfer leaves its purse and reaches the other actor's, creating no money",
      abs(second.money + guards_paid - 750.0) < 1e-9 and payee.record.income.get("transfer", 0.0) - received_before == 250.0
      and any(entry["command"] == "transfer" and entry["ok"] for entry in second.record.journal),
      (second.money, second.record.journal))
check("a command the game does not know is refused in the journal, not raised",
      any(entry["command"] == "no_such_command" and not entry["ok"] for entry in second.record.journal))

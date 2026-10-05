"""Complaint 340: a route's fleet grows when carriage pays more than the carriers cost and shrinks when it
does not: lift used over the year, and lift asked for and not carried, against the lift the fleet has."""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)

PARTNER = "han_china_100ad"


def lift_after_year(used_in, used_out, unmet):
    """(lift before, lift after) one year-end for a fleet that carried the stated shares of its lift."""
    game = sim(civ="rome_100ad", capital=1e9)
    game.foreign_economies = lambda: [PARTNER]
    route = game._foreign_economy_facts(PARTNER)["route"]
    before = game.foreign_lift_capacity_tonnes(PARTNER, route)
    ledger = game._foreign_ledger(PARTNER, create=True)
    ledger.update({"lift_year": game.state.scenario.year, "lift_tonnes_per_year": before,
                   "lift_used_in": used_in * before, "lift_used_out": used_out * before,
                   "lift_unmet": unmet * before})
    game.foreign_fleet_year_end()
    return before, game._foreign_ledger(PARTNER)["lift_tonnes_per_year"]


before, busy = lift_after_year(1.0, 1.0, 0.5)
check("a route with cargo left behind gains lift", busy > before * (1.0 - 0.2), (before, busy))
_before, steady = lift_after_year(1.0, 1.0, 0.0)
check("a route whose fleet is just full gains less than one with cargo left behind", steady < busy, (steady, busy))
_before, idle = lift_after_year(0.1, 0.05, 0.0)
check("a route whose carriers sit idle loses lift beyond wear", idle < steady, (idle, steady))
check("an idle fleet shrinks but not to nothing", 0.0 < idle < before, (before, idle))
_before, empty = lift_after_year(0.0, 0.0, 0.0)
check("a route that carries nothing keeps at least one carrier", empty > 0.0, empty)

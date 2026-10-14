"""Complaint 475: collection is a modest part of the state's coin revenue; a state that cannot meet its own
standing need lends nothing; unpaid army and office pay is arrears the state owes, paid first from later
revenue, and a mutinous army takes what it is owed."""
from .harness import *  # noqa: F401,F403

from sim.agents import group_servants
from sim.engine.agents_port import SimWorld


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def short_state():
    """Rome whose army costs more than any revenue and credit can pay, after its first year."""
    game = sim()
    game.civ["standing_army"] = 1.0e8
    game.state_treasury().money = 0.0
    one_year(game)
    return game, game.state_treasury()


# ---- collection is not most of the coin revenue ----------------------------------------------------------------
default = sim()
default_treasury = default.state_treasury()
one_year(default)
collected = default_treasury.record.income.get("taxation", 0.0)
collection_cost = default_treasury.record.outlays.get("tax_collection", 0.0)
check("collection costs well under half of the coin the state takes in its first year",
      collected > 0.0 and collection_cost < 0.5 * collected, (collection_cost, collected))

# ---- a state short of its standing need does not lend ------------------------------------------------------------
game, treasury = short_state()
check("the short state left need unpaid", sum(treasury.record.unfunded.values()) > 0.0, treasury.record.unfunded)
treasury.money = 1.0e12   # a windfall after the shortfall: the year's lenders still see a state that could not pay
check("a state that left its standing need unpaid offers no funds to lend",
      game.market_funds(SimWorld(game))["state"] == 0.0, game.market_funds(SimWorld(game)))
solvent = sim()
solvent_treasury = solvent.state_treasury()
solvent_treasury.money = 1.0e12
one_year(solvent)
check("a state that met its need and holds a reserve still does",
      solvent.market_funds(SimWorld(solvent))["state"] > 0.0, solvent.market_funds(SimWorld(solvent)))

# ---- unpaid army and office pay becomes arrears -------------------------------------------------------------------
game, treasury = short_state()
owed = treasury.record.arrears
check("the unpaid army pay is owed as arrears", owed.get("army", 0.0) > 0.0
      and abs(owed["army"] - treasury.record.unfunded["army"]) < 1e-6 * owed["army"], (owed, treasury.record.unfunded))
check("the money screen counts the arrears as owed by the state",
      game.capital_market_report()["the_state_owes"] >= round(sum(owed.values()), 1) - 1.0, game.capital_market_report())
before = dict(owed)
game.civ["standing_army"] = 0.0
treasury.money = 1.0e12
one_year(game)
check("later revenue pays the arrears first, in full when the purse covers them",
      all(treasury.record.arrears.get(line, 0.0) < 1e-6 for line in before), (before, treasury.record.arrears))

# ---- the army takes its arrears --------------------------------------------------------------------------------------
mutinous = sim()
mutinous_treasury = mutinous.state_treasury()
one_year(mutinous)
mutinous_treasury.record.unfunded = {line: 0.0 for line in mutinous_treasury.record.need}   # this year's pay was in full
mutinous_treasury.record.arrears = {"army": 60000.0}   # but a past shortfall is still owed
mutinous_treasury.record.loyalty = 0.0
mutinous_treasury.money = 1.0e9
held = mutinous_treasury.money
acted = group_servants.run_army_year(mutinous_treasury, SimWorld(mutinous))
check("an army owed arrears that has lost its loyalty takes them, though this year's pay was in full",
      acted["seized"] > 0.0 and mutinous_treasury.money < held, acted)
check("what the mutineers took is no longer owed",
      mutinous_treasury.record.arrears.get("army", 0.0) < 60000.0, mutinous_treasury.record.arrears)

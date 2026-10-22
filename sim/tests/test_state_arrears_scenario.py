"""Scenarios for Complaint 475 in a whole game: the first year's collection of a Rome game, and a state whose army costs
more than any revenue and credit can pay owes the pay as arrears, shows it in the money screen and pays it first from
later revenue. The rules are in test_state_arrears (and test_state_fiscal_response, test_state_surplus_rules)."""
from .harness import *  # noqa: F401,F403


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def short_state():
    """Rome whose army costs more than any revenue and credit can pay, after its first year."""
    game = sim()
    # the settled opening leaves nothing saved and the market at its ceiling (Complaints 607, 645), where a state weighing
    # deferred pay against cut services cuts; this scenario is about deferred pay, so it states the civilisation's own rate
    game.market_rate = lambda: float(game.civ["starting_interest_rate"])
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
check("scenario: collection costs well under half of the coin a Rome state takes in its first year",
      collected > 0.0 and collection_cost < 0.5 * collected, (collection_cost, collected))

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

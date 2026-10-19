"""Complaints 101, 112, 354, 478: a technique that halves a good's labour reaches a price and a quantity only
through producers that run it; split from test_real_output so each runs inside the topic limit."""
from .harness import *  # noqa: F401,F403
from .real_output_helpers import (GOOD, YEARS_CLOSED, YEARS_TO_ENTER, plain_node, traded_units, complete, run,
                                  close_years)

import copy

from sim.tests import economy_fixture
from sim.engine import prices as price_solver

control = sim(civ="rome_100ad", capital=1e9)
plain = plain_node(control)

# --- a technique that halves a good's labour reaches a price and a quantity only through producers that run it.
# The economy's producers gain the entries a technique in use allows (Complaint 478), so producers enter to make the
# good by it and, some years on, the market clears a larger quantity of it at a lower price than the same society's twin.
original = price_solver._default_production_entries()
patched = dict(original)
# the entry the incumbents make the good by
source_key = control._reference_entry(GOOD)
improved = copy.deepcopy(original[source_key])
improved["labour_hours"] = {trade: hours / 2.0 for trade, hours in improved["labour_hours"].items()}
improved["requires_node"] = plain
patched[GOOD + "_with_the_technique"] = improved
price_solver.reset_caches_for_tests()
price_solver._DEFAULT_PRODUCTION_ENTRIES = patched
# households buy a cheaper good in larger quantity out of a surplus, which the settled opening does not leave them
surplus = economy_fixture.surplus_game_openings()
surplus.__enter__()
try:
    game = sim(civ="rome_100ad", capital=1e9)   # the twin_years game below (nothing completed, same years closed) is its baseline
    price_before = game.goods_market.household_prices()[GOOD]
    other_before = {material: price for material, price in game.goods_market.household_prices().items()
                    if material in ("iron", "wheat_kg", "brick_1000")}
    complete(game, plain)
    check("a technique that is held but run by no producer changes no price",
          game.goods_market.household_prices()[GOOD] == price_before)
    run(game, plain)
    check("a technique one producer runs does not reprice the incumbents' cost of the good",
          game.goods_market.household_prices()[GOOD] == price_before)
    cost = game.entry_cost_ratio(GOOD + "_with_the_technique", GOOD)
    check("...but a producer making it by that entry makes it for less", cost < 0.75, cost)
    check("...and no good that does not use it changes price",
          all(game.goods_market.household_prices()[material] == price
              for material, price in other_before.items()), other_before)
    twin_years = sim(civ="rome_100ad", capital=1e9)
    close_years(game, 1)
    close_years(twin_years, 1)
    close_years(game, YEARS_TO_ENTER - 1)
    close_years(twin_years, YEARS_TO_ENTER - 1)
    check("a producer that makes the good by that entry and sells it lowers the price the market posts",
          game.goods_market.household_prices()[GOOD] < twin_years.goods_market.household_prices()[GOOD],
          (game.goods_market.household_prices()[GOOD], twin_years.goods_market.household_prices()[GOOD]))
    check("...and what the founder pays for a tonne of it falls with the price the market posts",
          game.goods_market.quote(GOOD)["buy_per_tonne"] < twin_years.goods_market.quote(GOOD)["buy_per_tonne"],
          (game.goods_market.quote(GOOD)["buy_per_tonne"], twin_years.goods_market.quote(GOOD)["buy_per_tonne"]))
    check("...and the bill for a larger order of it is smaller by the same technique",
          game.goods_market.purchase_cost(GOOD, 5.0)[0] < twin_years.goods_market.purchase_cost(GOOD, 5.0)[0],
          (game.goods_market.purchase_cost(GOOD, 5.0)[0], twin_years.goods_market.purchase_cost(GOOD, 5.0)[0]))
    check("...and the market clears a larger quantity of it than the same society without it",
          traded_units(game) > traded_units(twin_years), (traded_units(game), traded_units(twin_years)))
    check("...so real output rises, through that good",
          game.real_output_hours() > twin_years.real_output_hours() * 1.0001,
          (twin_years.real_output_hours(), game.real_output_hours()))
    check("...and output per head with it",
          game.real_output_per_head() > twin_years.real_output_per_head(),
          (twin_years.real_output_per_head(), game.real_output_per_head()))
finally:
    surplus.__exit__(None, None, None)
    price_solver.reset_caches_for_tests()


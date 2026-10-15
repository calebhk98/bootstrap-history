"""Complaints 101, 112, 354: output is the quantity of goods the market clears, valued at fixed
opening prices. A technology raises it only through the production entries it improves and the
goods those entries make; nothing counts completed technologies."""
from .harness import *  # noqa: F401,F403

import copy

from sim.engine import market_demand
from sim.tests import economy_fixture
from sim.engine.agents_port import SimWorld
from sim.engine import prices as price_solver
from sim.engine.data import calculated_goods_prices

GOOD = "fat_kg"
YEARS_CLOSED = 1   # the market is one agent-economy year to close, so the fewest years that show each property
YEARS_TO_ENTER = 5   # producers build plant to run a technique over some years before its goods reach the market


def plain_node(game):
    """A node that gates no production entry and earns nothing: completing it changes no recipe."""
    gates = price_solver.all_gate_nodes(price_solver._default_production_entries())
    done = game.state.projects.done
    return next(node_id for node_id in sorted(NODES)
                if node_id not in gates and node_id not in done and not NODES[node_id]["rev"])


def book_of_good(game):
    """The market book's entry for the good (the book is keyed by commodity)."""
    return game.state.economy.market_book[game._material_tag(GOOD)[0]]


def complete(game, node_id):
    game.state.projects.done.add(node_id)
    game._done_changed()


def run(game, node_id):
    """A producer runs the node's techniques: only then do they reach a price."""
    game.state.projects.operating.add(node_id)


def close_years(game, years):
    for _year in range(years):
        game._step_market()


# --- a technology that improves no entry does not raise output.
# The twin closes the same years with nothing completed: the market drifts a little by itself
# (capacity and trade follow the opening's own gaps), and only the difference is the technology's.
control, twin = sim(civ="rome_100ad", capital=1e9), sim(civ="rome_100ad", capital=1e9)
plain = plain_node(control)
complete(control, plain)
close_years(control, YEARS_CLOSED)
close_years(twin, YEARS_CLOSED)
check("a technology that improves no production entry leaves the goods' prices alone",
      dict(control.goods_market.household_prices()) == dict(twin.goods_market.household_prices()))
check("...and does not raise real output",
      control.real_output_hours() == twin.real_output_hours(),
      (control.real_output_hours(), twin.real_output_hours()))
check("...nor output per head", control.real_output_per_head() == twin.real_output_per_head(),
      (control.real_output_per_head(), twin.real_output_per_head()))

# --- a technique that halves a good's labour reaches a price and a quantity only through producers that run it.
# The economy's producers gain the entries a technique in use allows (Complaint 478), so producers enter to make the
# good by it and, some years on, the market clears a larger quantity of it at a lower price than the same society's twin.
original = price_solver._default_production_entries()
patched = dict(original)
source_key = next(key for key, entry in original.items() if GOOD in (entry.get("outputs") or {}))
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
    game = sim(civ="rome_100ad", capital=1e9)   # the twin above (nothing completed, same years closed) is its baseline
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
    close_years(game, YEARS_TO_ENTER)
    close_years(twin_years, YEARS_TO_ENTER)
    check("a producer that makes the good by that entry and sells it lowers the price the market posts",
          game.goods_market.household_prices()[GOOD] < twin_years.goods_market.household_prices()[GOOD],
          (game.goods_market.household_prices()[GOOD], twin_years.goods_market.household_prices()[GOOD]))
    check("...and the market clears a larger quantity of it than the same society without it",
          book_of_good(game)["traded_tonnes"] > 1.05 * book_of_good(twin_years)["traded_tonnes"],
          (book_of_good(game)["traded_tonnes"], book_of_good(twin_years)["traded_tonnes"]))
    check("...so real output rises, through that good",
          game.real_output_hours() > twin_years.real_output_hours() * 1.0001,
          (twin_years.real_output_hours(), game.real_output_hours()))
    check("...and output per head with it",
          game.real_output_per_head() > twin_years.real_output_per_head(),
          (twin_years.real_output_per_head(), game.real_output_per_head()))
finally:
    surplus.__exit__(None, None, None)
    price_solver.reset_caches_for_tests()

# --- society output is the sum of quantities times opening prices, in this civilisation's money.
game = sim(civ="rome_100ad", capital=1e9)
game._open_market_book()
book = game.state.economy.market_book
book["iron"]["traded_tonnes"] *= 1.5
book_of_good(game)["traded_tonnes"] *= 0.8
from sim.engine.real_output import opening_prices_in_hours
base_prices = opening_prices_in_hours(frozenset(game.state.projects.granted), game.civ, game._opening_farmed_hectares)
opening = market_demand.household_demand_by_material(
    base_prices, game._opening_population(), market_demand.MEAN_INCOME_HOURS_PER_CAPITA,
    game.civ, game.world_map)
total = 0.0
for material, units in opening.items():
    entry = book.get(game._material_tag(material)[0])
    if entry is None or units <= 0.0 or material not in base_prices:
        continue
    total += units * entry["traded_tonnes"] / entry["reference_tonnes"] * base_prices[material]
check("real output is the sum of quantities sold times opening prices",
      abs(game.real_output_hours() - total) <= 1e-9 * total, (game.real_output_hours(), total))
check("...and the lines it is made of add up to it",
      abs(sum(quantity * price for _material, quantity, price in game.real_output_lines())
          - game.real_output_hours()) <= 1e-9 * total)
_world = SimWorld(game)
_producing = max(0.0, game.population.working_age - _world.soldiers_under_arms()) / game.population.working_age
_expected = total * _producing * game.labour.money_per_labour_hour() * game.state.economy.output_factor
check("society output is that, less the share of working people under arms, in this civilisation's money",
      abs(_world.society_output() - _expected) <= 1e-9 * _expected, (_world.society_output(), _expected))
check("no field of the economy still counts technologies",
      not hasattr(game.state.economy, "economy") and not hasattr(game, "economy_index")
      and not hasattr(game, "output_volume_scale"))

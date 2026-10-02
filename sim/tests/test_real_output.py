"""Complaints 101, 112, 354: output is the quantity of goods the market clears, valued at fixed
opening prices. A technology raises it only through the production entries it improves and the
goods those entries make; nothing counts completed technologies."""
from .harness import *  # noqa: F401,F403

import copy

from sim.engine import market_demand
from sim.engine.actors import SimWorld
from sim.engine import prices as price_solver
from sim.engine.data import calculated_goods_prices

GOOD = "fat_kg"


def plain_node(game):
    """A node that gates no production entry and earns nothing: completing it changes no recipe."""
    gates = price_solver.all_gate_nodes(price_solver._default_production_entries())
    done = game.state.projects.done
    return next(node_id for node_id in sorted(NODES)
                if node_id not in gates and node_id not in done and not NODES[node_id]["rev"])


def complete(game, node_id):
    game.state.projects.done.add(node_id)
    game._done_changed()


def close_years(game, years):
    for _year in range(years):
        game._step_market()


# --- a technology that improves no entry does not raise output.
# The twin closes the same years with nothing completed: the market drifts a little by itself
# (capacity and trade follow the opening's own gaps), and only the difference is the technology's.
control, twin = sim(civ="rome_100ad", capital=1e9), sim(civ="rome_100ad", capital=1e9)
plain = plain_node(control)
complete(control, plain)
close_years(control, 5)
close_years(twin, 5)
check("a technology that improves no production entry leaves the goods' prices alone",
      dict(control.goods_market.household_prices()) == dict(twin.goods_market.household_prices()))
check("...and does not raise real output",
      control.real_output_hours() == twin.real_output_hours(),
      (control.real_output_hours(), twin.real_output_hours()))
check("...nor output per head", control.real_output_per_head() == twin.real_output_per_head(),
      (control.real_output_per_head(), twin.real_output_per_head()))

# --- a technique that halves a good's labour lowers its price and raises what is sold.
original = price_solver._default_production_entries()
patched = dict(original)
source_key = next(key for key, entry in original.items() if GOOD in (entry.get("outputs") or {}))
improved = copy.deepcopy(original[source_key])
improved["labour_hours"] = {trade: hours / 2.0 for trade, hours in improved["labour_hours"].items()}
improved["requires_node"] = plain
patched[GOOD + "_with_the_technique"] = improved
price_solver.reset_caches_for_tests()
price_solver._DEFAULT_PRODUCTION_ENTRIES = patched
try:
    game, twin = sim(civ="rome_100ad", capital=1e9), sim(civ="rome_100ad", capital=1e9)
    price_before = game.goods_market.household_prices()[GOOD]
    other_before = {material: price for material, price in game.goods_market.household_prices().items()
                    if material in ("iron", "wheat_kg", "brick_1000")}
    game._open_market_book()
    sold_before = game.state.economy.market_book[GOOD]["traded_tonnes"]
    output_before = game.real_output_hours()
    complete(game, plain)
    price_after = game.goods_market.household_prices()[GOOD]
    check("a technique that halves a good's labour lowers that good's price",
          price_after < 0.75 * price_before, (price_before, price_after))
    check("...and no good that does not use it changes price",
          all(game.goods_market.household_prices()[material] == price
              for material, price in other_before.items()), other_before)
    check("households want more of the cheaper good",
          game.household_demand_ratio(GOOD) > 1.05, game.household_demand_ratio(GOOD))
    close_years(game, 6)
    close_years(twin, 6)
    sold_after = game.state.economy.market_book[GOOD]["traded_tonnes"]
    check("...and the market clears a larger quantity of it than the same society without it",
          sold_after > 1.05 * twin.state.economy.market_book[GOOD]["traded_tonnes"],
          (sold_before, sold_after, twin.state.economy.market_book[GOOD]["traded_tonnes"]))
    check("...so real output rises, through that good",
          game.real_output_hours() > twin.real_output_hours() * 1.0001,
          (twin.real_output_hours(), game.real_output_hours()))
    check("...and output per head with it",
          game.real_output_per_head() > 1.0, game.real_output_per_head())
finally:
    price_solver.reset_caches_for_tests()

# --- society output is the sum of quantities times opening prices, in this civilisation's money.
game = sim(civ="rome_100ad", capital=1e9)
game._open_market_book()
book = game.state.economy.market_book
book["iron"]["traded_tonnes"] *= 1.5
book[GOOD]["traded_tonnes"] *= 0.8
granted = frozenset(game.state.projects.granted)
base_prices = {material: price for material, price in calculated_goods_prices(
    granted, civilization_id="rome_100ad", civilization=game.civ, money_per_labour_hour=1.0).items()
    if price > 0.0}
opening = market_demand.household_demand_by_material(
    {material: price for material, price in base_prices.items() if game.material_price_basis(material) != "mature"},
    game._opening_population(), market_demand.MEAN_INCOME_HOURS_PER_CAPITA)
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
check("society output is that, in this civilisation's money",
      abs(SimWorld(game).society_output() - total * game.money_per_labour_hour()
          * game.state.economy.output_factor) <= 1e-9 * total * game.money_per_labour_hour(),
      (SimWorld(game).society_output(), total * game.money_per_labour_hour()))
check("no field of the economy still counts technologies",
      not hasattr(game.state.economy, "economy") and not hasattr(game, "economy_index")
      and not hasattr(game, "output_volume_scale"))

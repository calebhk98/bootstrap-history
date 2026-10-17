"""Complaints 101, 112, 354: output is the quantity of goods the market clears, valued at fixed
opening prices. A technology raises it only through the production entries it improves and the
goods those entries make; nothing counts completed technologies."""
from .harness import *  # noqa: F401,F403
from .real_output_helpers import (GOOD, YEARS_CLOSED, YEARS_TO_ENTER, plain_node, book_of_good, complete, run,
                                  baseline_the_twin, close_years)

from sim.engine import market_demand
from sim.engine.agents_port import SimWorld

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

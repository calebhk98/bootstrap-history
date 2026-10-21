"""Scenarios (Complaints 38 and 640), Rome: a material nobody makes cannot be bought; the derived node revenue and the
opening basket are finite. The rules are in test_whole_game_no_seller_no_price. Slow topic: it builds a game and
derives the node revenue of the whole tree.

It also prints what the change does to node revenue and to the opening basket, so the re-measure is one
command: `python3 -m sim.tests --slow --only whole_game_no_seller_no_price_scenario`."""
from .harness import *  # noqa: F401,F403

import math

from sim.engine import data, energy_prices

game = sim(civ="rome_100ad", capital=1e9)
market = game.goods_market
household = market.household_prices()
sellers = {material: market.offered_by(material) for material in household}

check("a material no home technique and no partner makes has no price and cannot be bought",
      all(not market.can_be_bought(material) for material in ("cobalt_kg", "germanium_g")
          if material not in household),
      [material for material in ("cobalt_kg", "germanium_g") if material not in household and market.can_be_bought(material)])

# Rome opens with no partner-sold material (the measurement below prints how many), so an import's bounds are not
# a played-game check here: they are test_whole_game_no_seller_no_price (import_tonnes_left).
partner_sold = sorted(material for material, seller in sellers.items() if seller not in (None, "home"))

# measurement: the derived revenue of every node with heat grades nothing held supplies priced out
civ = data.load_civ("rome_100ad")
_tree, document, nodes, _wages, goods = data.load(civ["starting_techs"], "rome_100ad")
energy = energy_prices.graded(civ["starting_techs"], document, goods, "rome_100ad")
check("a grade of heat no technique Rome holds supplies has no band", all(
    (carrier, required) not in energy.bands for (carrier, required) in energy.unreachable))
revenues = [node["rev_hours"] for node in nodes.values() if node.get("_revenue_basis") == "output"]
check("every derived node revenue is finite", all(math.isfinite(revenue) for revenue in revenues))
basket = game.base_basket()
opening_cost = sum(units * basket["prices"][material] for material, units in basket["units"].items())
print("MEASURE rome_100ad: derived-output nodes %d, total rev_hours %.1f, unreachable heat grades %d, "
      "imported materials %d, opening basket cost %.1f hours a year"
      % (len(revenues), sum(revenues), len(energy.unreachable), len(partner_sold), opening_cost))
check("the opening basket is priced", opening_cost > 0.0 and math.isfinite(opening_cost))

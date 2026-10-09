"""Complaints/38, whole game: a price needs a seller, and an import is bounded by what the partner makes and
the carriers lift. Slow topic: it builds a game and derives the node revenue of the whole tree for Rome.

It also prints what the change does to node revenue and to the opening basket, so the re-measure is one
command: `python3 -m sim.tests --slow --only whole_game_no_seller_no_price`."""
from .harness import *  # noqa: F401,F403

import math

from sim.engine import data, energy_prices

game = sim(civ="rome_100ad", capital=1e9)
market = game.goods_market
household = market.household_prices()
sellers = {material: market.offered_by(material) for material in household}

check("every material households are asked to pay for has a seller in reach",
      all(seller is not None for seller in sellers.values()),
      sorted(material for material, seller in sellers.items() if seller is None)[:10])
check("a material no home technique and no partner makes has no price and cannot be bought",
      all(not market.can_be_bought(material) for material in ("cobalt_kg", "germanium_g")
          if material not in household),
      [material for material in ("cobalt_kg", "germanium_g") if material not in household and market.can_be_bought(material)])

partner_sold = sorted(material for material, seller in sellers.items() if seller not in (None, "home"))
available = {material: market.import_tonnes_available(material) for material in partner_sold}
check("every import has a finite, non-negative volume of at most what its partner makes and holds",
      all(tonnes is not None and 0.0 <= tonnes <= game.foreign_supply_tonnes(sellers[material], material) + 1e-9
          for material, tonnes in available.items()),
      [(material, tonnes) for material, tonnes in available.items()
       if tonnes is None or tonnes > game.foreign_supply_tonnes(sellers[material], material) + 1e-9][:5])
check("...and of at most the lift the route's carriers have left",
      all(tonnes <= game.foreign_lift_left_tonnes(sellers[material], market._route_from(sellers[material]))[0] + 1e-9
          for material, tonnes in available.items()),
      [material for material, tonnes in available.items()
       if tonnes > game.foreign_lift_left_tonnes(sellers[material], market._route_from(sellers[material]))[0] + 1e-9][:5])
check("a quote of an import states its own volume, not the home output curve's",
      all(abs(market.quote(material)["market_available_tonnes_per_year"] - available[material]) < 1e-9
          for material in partner_sold if market.quote(material) is not None))
check("the market screen calls a partner-sold material imported",
      all(game.material_price_basis(material) == "imported" for material in partner_sold))

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

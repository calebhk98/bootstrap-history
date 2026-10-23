"""Scenario (Complaints 38 and 640), Rome: a material nobody makes cannot be bought. The rules are in
test_whole_game_no_seller_no_price (the market's books) and test_heat_grade_has_a_supplier (a grade of heat nobody supplies
has no band); the opening basket is held by test_opening_basket_agrees."""
from .harness import *  # noqa: F401,F403

game = sim(civ="rome_100ad", capital=1e9)
market = game.goods_market
household = market.household_prices()

check("a material no home technique and no partner makes has no price and cannot be bought",
      all(not market.can_be_bought(material) for material in ("cobalt_kg", "germanium_g")
          if material not in household),
      [material for material in ("cobalt_kg", "germanium_g") if material not in household and market.can_be_bought(material)])

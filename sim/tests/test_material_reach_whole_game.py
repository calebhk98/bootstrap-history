"""Complaint 480, scenario (Complaint 640 audit): in a fresh game a good with no deposit and no producer plant (alum)
sits on a named route. The routes are rule tests in test_material_reach; this holds that the shipped data places three
real goods on the three routes, and that the quote and the throttle read one market figure."""
from .harness import *  # noqa: F401,F403

game = sim(civ="rome_100ad", events=False, capital=1e9)
routes = {material: game.material_supply_route(material)["route"]
          for material in ("alum_kg", "cobalt_kg", "wheat_kg")}
check("a good a held technique makes and no producer runs is makeable, not out of the market",
      routes["alum_kg"] == "makeable", routes)
check("a good no one in reach makes or sells is unavailable", routes["cobalt_kg"] == "unavailable", routes)
check("a good the market brings is on the market route", routes["wheat_kg"] == "market", routes)
check("the quote's volume and the throttle's market tonnes agree",
      game.goods_market.quote("alum_kg")["market_available_tonnes_per_year"]
      == game._material_market_tonnes("alum_kg"))

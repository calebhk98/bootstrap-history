"""Complaint 480: a fresh game's goods with no deposit and no producer plant (alum) used to throttle work to the
floor with the one line "the market is out of it". Each now sits on a named route and the shortage says why."""
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
game.step()
remedy = game.shortage_remedy("alum_kg")
check("a shortage of a good nothing makes names the cause",
      game.material_supply_route("alum_kg")["route"] == "makeable", remedy)
check("...and a good nobody can sell is told as unavailable",
      game.material_supply_route("cobalt_kg")["route"] == "unavailable", game.shortage_remedy("cobalt_kg"))

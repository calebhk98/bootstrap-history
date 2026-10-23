"""Complaint 190: the light and amusement needs that the late-game works lean on, read from the data, and the typed
`settle` lines. Settled colonies (founding, the yearly step, save and load, commands) are test_colony_wiring on stand-ins."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.engine.need_data import load_needs
from sim.labour.api import production_data
from sim.world import need_basket

from sim.ui.proto.typed import parse_typed

check("the typed line `settle <tile>` reads", parse_typed("settle %s" % "tile_1")[0] == {"cmd": "settle", "tile": "tile_1"})
check("the typed line `settle` alone lists", parse_typed("settle")[0] == {"cmd": "settle"})

# ---- light is its own need, and play for stakes is one too --------------------------------------------------------
needs = load_needs(ROOT)
check("warmth and light are each a need", "warmth" in needs["needs"] and "light" in needs["needs"], sorted(needs["needs"]))
check("fuel is for warmth", all("warmth" in needs["goods"][fuel]["satisfies"] for fuel in ("firewood_kg", "charcoal_kg", "coal_kg", "peat_kg")))
basket = need_basket.make_basket(needs, production_data())
serving = {need.need_id: {good for good, _effect in need.goods} for need in basket.needs}
check("a candle, an oil lamp and an electric lamp are the ways to light a room",
      {"light_tallow_candle", "light_oil_lamp", "light_electric_lamp"} <= serving["light"], serving["light"])
check("a table at a gaming house and a lottery chance are the ways to play for stakes",
      {"gaming_table_hour", "lottery_chance"} <= serving["amusement"], serving["amusement"])
production = production_data()
check("the tallow candle needs no technology, so every society can light a room",
      production["light_tallow_candle"]["requires_node"] is None)
check("the electric lamp draws generated electricity",
      production["light_electric_lamp"].get("electrical_mj", 0.0) > 0.0 and production["light_electric_lamp"]["requires_node"] == "hom_electric_lighting")
check("the gaming house and the lottery earn their takings from the play they serve",
      NODES["fin_gambling_house"]["rev"] > 0 and NODES["fin_lottery"]["rev"] > 0,
      (NODES["fin_gambling_house"]["rev"], NODES["fin_lottery"]["rev"]))

"""Food, housing, trade schools, demographics, and durable material stock."""
from .harness import *
from engine.proto.render import render_pretty
from engine.proto.typed import parse_typed

check("typed economic levers reach their protocol actions",
      parse_typed("buy farm 120")[0] == {"cmd": "buy", "what": "farm", "n": 120}
      and parse_typed("buy housing 5")[0] == {"cmd": "buy", "what": "housing", "n": 5}
      and parse_typed("buy school smith 2")[0]
          == {"cmd": "buy", "what": "school", "material": "smith", "n": 2}
      and parse_typed("materials")[0] == {"cmd": "materials"}
      and parse_typed("sell iron 5")[0]
          == {"cmd": "sell", "material": "iron", "n": 5})


s = sim(capital=1_000_000)
wage0 = s.annual_wage("artisan")
reply = S._agent_dispatch(s, NODES, {"cmd": "buy", "what": "farm", "n": 120})
check("farmland is a direct lever that lowers food costs and wages",
      reply["ok"] and reply["food_cost_factor"] < 1
      and s.annual_wage("artisan") < wage0, reply)

room0 = s.supervision_room()
reply = S._agent_dispatch(s, NODES, {"cmd": "buy", "what": "housing", "n": 5})
check("worker housing directly expands household capacity",
      reply["ok"] and s.supervision_room() == room0 + 5, reply)

s.trades_created.add("chemist")
s._add_labour_pressure("chemist", 2_000)
scarcity0 = s.labour_price_factor("chemist")
reply = S._agent_dispatch(s, NODES, {"cmd": "buy", "what": "school",
                                     "trade": "chemist", "n": 2})
check("a named trade school makes its profession more common",
      reply["ok"] and s.market_supply("chemist") >= 4_000
      and s.labour_price_factor("chemist") < scarcity0, reply)

pop = S._agent_dispatch(s, NODES, {"cmd": "population"})
check("population exposes national, reachable, and employed trade demographics",
      pop["ok"] and all(field in pop["trades"][0] for field in
                        ("estimated_in_the_country", "within_your_reach", "you_employ")),
      pop)

s = sim()
s._own_production_tags = lambda: {("iron", "mine:iron")}
s._own_material_supply = lambda tag: 100.0 if tag == "mine:iron" else 0.0
s._material_market_tonnes = lambda material: 0.0
s.annual_material_demand = lambda: {}
s.resource_throttle()
s.resource_throttle()
one_year = s.material_stock_t("iron")
s.year += 1
s.resource_throttle()
check("unused mine output banks once per year rather than once per query",
      one_year == 100.0 and s.material_stock_t("iron") == 200.0,
      (one_year, s.material_stock_t("iron")))

s = sim()
s._material_stock()["iron"] = 100.0
s.year += 2
s.annual_material_demand = lambda: {"iron_bar_kg": 50.0}
s._material_market_tonnes = lambda material: 0.0
s._own_material_supply = lambda tag: 0.0
check("old iron inventory covers later demand without current production",
      s.resource_throttle() == 1.0 and abs(s.material_stock_t("iron") - 50.0) < 1e-6,
      (s.throttle, s.material_stock_t("iron")))

report = S._agent_dispatch(s, NODES, {"cmd": "materials"})
iron = next(material_row for material_row in report["materials"] if material_row["material"] == "iron")
check("materials reports stock, flow, demand, and buy/sell values",
      iron["stock_on_hand_tonnes"] == 50.0
      and all(iron[field] is not None for field in
              ("own_production_tonnes_per_year", "current_demand_tonnes_per_year",
               "buy_per_tonne", "sell_per_tonne")), iron)
check("the readable materials screen exposes inventory",
      "MATERIAL STOCKS" in render_pretty("materials", report), report)

s = sim(capital=1_000_000)
bought = S._agent_dispatch(s, NODES, {"cmd": "buy", "what": "material",
                                      "material": "iron", "n": 1})
sold = S._agent_dispatch(s, NODES, {"cmd": "sell", "material": "iron", "n": 0.5})
check("material stock can be explicitly bought and sold",
      bought["ok"] and sold["ok"] and abs(s.material_stock_t("iron") - 0.5) < 1e-6,
      (bought, sold))

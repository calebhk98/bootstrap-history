"""SCENARIO: food, housing, trade schools, demographics, and durable material stock. The typed-command parse is a rule in
test_typed_front_end; the stock accounting of the material throttle (banking once per year) is a rule in
test_material_throttle_rules. Two scenarios: the levers pulled through the protocol on one game, and the materials report
with explicit buying and selling."""
from .harness import *
from sim.ui.proto.render import render_pretty

s = unopened_sim(capital=1_000_000)
reply = S._agent_dispatch(s, NODES, {"cmd": "buy", "what": "farm", "n": 120})
# --- SCENARIO: the levers, pulled on one game
check("scenario: farmland is a direct lever that lowers food costs", reply["ok"] and reply["food_cost_factor"] < 1, reply)

room0 = s.labour.supervision_room()
reply = S._agent_dispatch(s, NODES, {"cmd": "buy", "what": "housing", "n": 5})
check("scenario: worker housing directly expands household capacity",
      reply["ok"] and s.labour.supervision_room() == room0 + 5, reply)

s.trades_created.add("chemist")
s.labour.market.press("chemist", 2_000)
scarcity0 = s.labour.market.price_factor("chemist")
reply = S._agent_dispatch(s, NODES, {"cmd": "buy", "what": "trade_school",
                                     "trade": "chemist", "n": 2})
check("scenario: a named trade school makes its profession more common",
      reply["ok"] and s.labour.market_supply("chemist") >= 4_000
      and s.labour.market.price_factor("chemist") < scarcity0, reply)

pop = S._agent_dispatch(s, NODES, {"cmd": "population"})
check("scenario: population exposes national, reachable, and employed trade demographics",
      pop["ok"] and all(field in pop["trades"][0] for field in
                        ("estimated_in_the_country", "within_your_reach", "you_employ")),
      pop)

# --- SCENARIO: the materials report, and explicit buying and selling
s = unopened_sim()
s._material_stock()["iron"] = 50.0
report = S._agent_dispatch(s, NODES, {"cmd": "materials"})
iron = next(material_row for material_row in report["materials"] if material_row["material"] == "iron")
check("scenario: materials reports stock, flow, demand, and buy/sell values",
      iron["stock_on_hand_tonnes"] == 50.0
      and all(iron[field] is not None for field in
              ("own_production_tonnes_per_year", "current_demand_tonnes_per_year",
               "buy_per_tonne", "sell_per_tonne")), iron)
# presentation: the readable materials screen carries its heading
check("the readable materials screen exposes inventory",
      "MATERIAL STOCKS" in render_pretty("materials", report), report)

s = unopened_sim(capital=1_000_000)
bought = S._agent_dispatch(s, NODES, {"cmd": "buy", "what": "material",
                                      "material": "iron", "n": 1})
sold = S._agent_dispatch(s, NODES, {"cmd": "sell", "material": "iron", "n": 0.5})
check("scenario: material stock can be explicitly bought and sold",
      bought["ok"] and sold["ok"] and abs(s.material_stock_t("iron") - 0.5) < 1e-6,
      (bought, sold))

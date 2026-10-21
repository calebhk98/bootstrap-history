"""commodities_wired_in: copper_wire_kg, wire_drawn_kg and gold_kg are real material keys that many nodes draw, and are
tracked by the material checks (COMMODITIES.md section 0/7.1). The rules are called on a ledger and on a stub game; the
throttle wiring on a whole game is test_commodities_wired_in_scenario."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403

from sim.engine.economy_freight import FreightMixin
from sim.engine.economy_materials import MaterialSupplyMixin

# --- supply_override actually overrides, rather than being silently ignored alongside commodities.json's own (much
# larger) national estimate.
override_led = COMMOD.CommodityLedger(supply_override={"copper": 10.0})
tiny = override_led.propagate_demand("copper_wire", 100.0)
check("supply_override replaces the national estimate, not just adds to it: "
      "10 t/yr of copper cannot deliver 100 t/yr of wire",
      tiny["met_fraction"] < 0.2, tiny["met_fraction"])
plain_led = COMMOD.CommodityLedger()
plenty = plain_led.propagate_demand("copper_wire", 100.0)
check("...while the SAME call with no override still reads commodities.json's "
      "own (much larger) national figure, exactly as before",
      plenty["met_fraction"] > tiny["met_fraction"],
      (plenty["met_fraction"], tiny["met_fraction"]))

# --- wire_chain_report hands the ledger THIS game's reachable copper (its own mines plus what the market will sell),
# so the same order is met in one society and not in another, and the shortfall is attributed to copper.
def wire_report(own_t, market_t, order_t):
    game = types.SimpleNamespace(_own_material_supply=lambda tag: own_t, _material_market_tonnes=lambda material: market_t)
    return FreightMixin.wire_chain_report(game, order_t)


rep_modest = wire_report(40.0, 160.0, 5.0)
check("a modest copper wire order is fully met when the copper is reachable",
      rep_modest["met_fraction"] > 0.999, rep_modest["met_fraction"])
rep_big = wire_report(40.0, 160.0, 2000.0)
check("an industrial copper wire order is NOT fully met, and the shortfall is attributed to copper, "
      "not to wire-drawing capacity",
      rep_big["met_fraction"] < 0.95 and rep_big["children"]["copper"]["bottleneck"] == "copper"
      and rep_big["bottleneck"] is None, (rep_big["met_fraction"], rep_big["bottleneck"]))
rep_poor = wire_report(4.0, 16.0, 2000.0)
check("a society with less reach to copper gets a worse chain report for the identical request",
      rep_poor["children"]["copper"]["own_capacity_t"] < rep_big["children"]["copper"]["own_capacity_t"]
      and rep_poor["met_fraction"] < rep_big["met_fraction"],
      (rep_poor["children"]["copper"]["own_capacity_t"], rep_big["children"]["copper"]["own_capacity_t"]))
check("a negative order is read as none", wire_report(40.0, 160.0, -3.0)["met_fraction"] >= 0.999, "negative order refused")

# --- the aggregation: material keys drawing on the SAME supply are summed before being compared to it, not checked one at
# a time against the whole supply each time (_demand_by_supply_tag).
grouper = types.SimpleNamespace(MATERIAL_CHECKS=MaterialSupplyMixin.MATERIAL_CHECKS)
grouper._material_commodity_map = lambda: {}
grouper._material_tag = lambda material: MaterialSupplyMixin._material_tag(grouper, material)
grouped = MaterialSupplyMixin._demand_by_supply_tag(grouper, {
    "copper_kg": 3.0, "copper_wire_kg": 4.0, "wire_drawn_kg": 0.0, "iron_bar_kg": 1.0, "iron_ore_kg": 2.0,
    "charcoal_kg": 5.0, "firewood_kg": 9.0})
check("copper_kg and copper_wire_kg demand are summed under one shared supply, not checked independently",
      grouped[("copper", "mine:copper")] == 7.0, dict(grouped))
check("...and iron_bar_kg and iron_ore_kg (already sharing one supply) are summed the same way",
      grouped[("iron", "mine:iron")] == 3.0, dict(grouped))
check("...while charcoal_kg and firewood_kg, which draw on the SAME forest at DIFFERENT yields per hectare, "
      "stay in separate groups rather than being summed together",
      grouped[("charcoal", "forest1")] == 5.0 and grouped[("charcoal", "forest4")] == 9.0,
      (grouped[("charcoal", "forest1")], grouped[("charcoal", "forest4")]))
check("a key nothing has named is a one-member commodity of itself",
      MaterialSupplyMixin._demand_by_supply_tag(grouper, {"aluminium_kg": 2.0})[("aluminium_kg", "mine:aluminium_kg")] == 2.0,
      "ungrouped")

# --- gold is a tracked commodity: fin_central_bank's 1,000 kg of gold_kg was invisible to every material check.
check("gold_kg is covered by MATERIAL_CHECKS, the same way copper_kg is",
      MaterialSupplyMixin.MATERIAL_CHECKS.get("gold_kg") == ("gold", "mine:gold"),
      MaterialSupplyMixin.MATERIAL_CHECKS.get("gold_kg"))
check("gold has a MARKET_SHARE entry sourced from commodities.json's own gold figure, so the two files do not disagree",
      MaterialSupplyMixin.MARKET_SHARE.get("gold") == COMMOD.load_commodities()["gold"]["market_share"],
      (MaterialSupplyMixin.MARKET_SHARE.get("gold"), COMMOD.load_commodities()["gold"]["market_share"]))

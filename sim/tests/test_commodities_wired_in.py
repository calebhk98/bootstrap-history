"""commodities_wired_in: copper_wire_kg, wire_drawn_kg and gold_kg are real material keys that many nodes draw, and are
tracked by the material checks (COMMODITIES.md section 0/7.1). The rules are called on a ledger and on a stub game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.materials import constants as material_constants
from sim.tests import materials_stand_in

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

# --- the aggregation: material keys drawing on the SAME supply are summed before being compared to it, not checked one at
# a time against the whole supply each time (_demand_by_supply_tag).
grouper = materials_stand_in.build()
grouped = grouper.demand_by_supply_tag({
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
      grouper.demand_by_supply_tag({"aluminium_kg": 2.0})[("aluminium_kg", "mine:aluminium_kg")] == 2.0,
      "ungrouped")

# --- gold is a tracked commodity: fin_central_bank's 1,000 kg of gold_kg was invisible to every material check.
check("gold_kg is covered by MATERIAL_CHECKS, the same way copper_kg is",
      material_constants.MATERIAL_CHECKS.get("gold_kg") == ("gold", "mine:gold"),
      material_constants.MATERIAL_CHECKS.get("gold_kg"))
check("gold has a MARKET_SHARE entry sourced from commodities.json's own gold figure, so the two files do not disagree",
      material_constants.MARKET_SHARE.get("gold") == COMMOD.load_commodities()["gold"]["market_share"],
      (material_constants.MARKET_SHARE.get("gold"), COMMOD.load_commodities()["gold"]["market_share"]))

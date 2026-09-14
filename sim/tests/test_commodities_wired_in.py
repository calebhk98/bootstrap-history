"""commodities_wired_in: split verbatim from the old test_regressions.py (original lines 3535-3635).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# COMMODITIES, WIRED IN (COMMODITIES.md section 0/7.1). copper_wire_kg,
# wire_drawn_kg and gold_kg are real material keys 36+ real nodes draw, and
# were invisible to resource_throttle() before this pass. economy.py now
# calls commodities.py's own propagate_demand() (via wire_chain_report()),
# handed THIS Sim's live copper numbers through CommodityLedger's new
# supply_override, instead of a second, disconnected estimate.
# =============================================================================

# --- supply_override actually overrides, rather than being silently ignored
# alongside commodities.json's own (much larger) national estimate.
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

# --- economy.py.wire_chain_report(): the real worked example, on a real Sim.
s_wire = sim(capital=400000.0)
rep_modest = s_wire.wire_chain_report(5.0)
check("a modest copper wire order is fully met by an ordinary Roman buyer's "
      "own copper market access",
      rep_modest["met_fraction"] > 0.999, rep_modest["met_fraction"])
rep_big = s_wire.wire_chain_report(2000.0)
check("an industrial copper wire order is NOT fully met, and the shortfall "
      "is attributed to copper, not to wire-drawing capacity",
      rep_big["met_fraction"] < 0.95
      and rep_big["children"]["copper"]["bottleneck"] == "copper"
      and rep_big["bottleneck"] is None,
      (rep_big["met_fraction"], rep_big["bottleneck"]))

# --- a poorer, less-connected civilization reaches less copper than Rome for
# the SAME request, because wire_chain_report() reads THIS Sim's own numbers
# (mineral_scale, MARKET_SHARE, mine_capacity), not one flat figure.
s_norse = sim(civ="norse_900ad", capital=400000.0)
rep_norse = s_norse.wire_chain_report(2000.0)
check("a civilization with less reach to copper gets a worse chain report "
      "for the identical request, not the same one",
      rep_norse["children"]["copper"]["own_capacity_t"]
      < rep_big["children"]["copper"]["own_capacity_t"],
      (rep_norse["children"]["copper"]["own_capacity_t"],
       rep_big["children"]["copper"]["own_capacity_t"]))

# --- resource_throttle() now actually throttles on copper_wire_kg: a
# mechanism-level check, since no realistic combination of real nodes'
# kilogram-scale wire draws (the largest, el2_ring_main_distribution, is
# 8,000 kg spread over 4 years) actually reaches the hundreds of tonnes a
# year it takes to outrun Rome's own copper market - the same reason
# COMMODITIES.md section 7.1's own worked example and demo_commodities.py
# both had to use an illustrative industrial-scale figure rather than sum
# real nodes. This proves the WIRING (a large copper_wire_kg demand binds
# resource_throttle on "copper"), not a claim about ordinary play.
s_thr = sim(capital=1e9)
s_thr._material_demand_cache = {"copper_wire_kg": 100000.0}
s_thr.annual_material_demand = lambda: s_thr._material_demand_cache
thr = s_thr.resource_throttle()
check("a copper_wire_kg demand far beyond the copper market binds "
      "resource_throttle on copper, where before this key was not "
      "tracked at all",
      thr < 0.95 and s_thr.binding == "copper", (thr, s_thr.binding))

# --- the aggregation fix: three material keys drawing on the SAME copper
# supply are summed before being compared to it, not checked one at a time
# against the whole supply each time (_demand_by_supply_tag).
s_agg = sim(capital=1e9)
grouped = s_agg._demand_by_supply_tag({"copper_kg": 3.0, "copper_wire_kg": 4.0,
                                       "wire_drawn_kg": 0.0,
                                       "iron_bar_kg": 1.0, "iron_ore_kg": 2.0,
                                       "charcoal_kg": 5.0, "firewood_kg": 9.0})
check("copper_kg and copper_wire_kg demand are summed under one shared "
      "supply, not checked independently",
      grouped[("copper", "mine:copper")] == 7.0, dict(grouped))
check("...and iron_bar_kg/iron_ore_kg (already sharing one supply) are "
      "summed the same way",
      grouped[("iron", "mine:iron")] == 3.0, dict(grouped))
check("...while charcoal_kg and firewood_kg, which draw on the SAME forest "
      "at DIFFERENT yields per hectare, stay in separate groups rather "
      "than being summed together",
      grouped[("charcoal", "forest1")] == 5.0
      and grouped[("charcoal", "forest4")] == 9.0,
      (grouped[("charcoal", "forest1")], grouped[("charcoal", "forest4")]))

# --- gold is now a tracked commodity: fin_central_bank's 1,000 kg of
# gold_kg was invisible to every material check before this pass, despite
# Sim.open_mine("gold", ...) already existing.
check("gold_kg is now covered by MATERIAL_CHECKS, the same way copper_kg is",
      s_agg.MATERIAL_CHECKS.get("gold_kg") == ("gold", "mine:gold"),
      s_agg.MATERIAL_CHECKS.get("gold_kg"))
check("gold has a MARKET_SHARE entry sourced from commodities.json's own "
      "gold figure, so the two files do not disagree",
      s_agg.MARKET_SHARE.get("gold")
      == COMMOD.load_commodities()["gold"]["market_share"],
      (s_agg.MARKET_SHARE.get("gold"),
       COMMOD.load_commodities()["gold"]["market_share"]))


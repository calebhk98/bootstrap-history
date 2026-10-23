"""Rule checks for the diffusion categories (SCENARIO wiring is in test_craftsmen_wording): the share of a technology
spread after an age, the medical relief a spread and a capable state give, and the data the categories key off. Every figure is
built here or read from the data; no game is built."""
QUICK_TOPIC = True

from .harness import check, NODES, _hazard

from sim.engine.diffusion_rules import medical_relief, spread_share

_FOOD_NODE, _MED_NODES, _MIL_NODES2, _INFO_NODE = (
    "crop_rotation",
    ["sanitation_antisepsis", "med_quarantine_sanitation", "germ_theory",
     "md2_vaccine_smallpox"],
    ["gunpowder", "mil_artillery_piece"],
    "printing_press",
)
check("the four diffusion categories this section reads are real nodes with "
      "the traits civ_diffusion keys off",
      NODES[_FOOD_NODE]["traits"].__contains__("food")
      and all("medical" in NODES[node_id]["traits"] for node_id in _MED_NODES)
      and all("military" in NODES[node_id]["traits"] for node_id in _MIL_NODES2)
      and "information" in NODES[_INFO_NODE]["traits"],
      (_FOOD_NODE, _MED_NODES, _MIL_NODES2, _INFO_NODE))

# --- spread_share: zero at once, half after one half-life, bounded at all of it.
check("nothing has spread the instant a technology completes - diffusion takes time",
      spread_share(0.0, 25.0) == 0.0)
check("half is spread after one half-life, and a quarter remains after two",
      abs(spread_share(25.0, 25.0) - 0.5) < 1e-12 and abs(spread_share(50.0, 25.0) - 0.75) < 1e-12)
check("however long it has had, the share never exceeds one", spread_share(1.0e6, 25.0) <= 1.0)
check("a negative age (the clock before completion) spreads nothing", spread_share(-5.0, 25.0) == 0.0)


check("medical diffusion relief has no fixed ceiling: full coverage with a capable state removes the epidemic entirely",
      medical_relief(1.0, 0.5, 1.0) >= 1.0)
check("...with no state the guidance is followed by the base share alone",
      abs(medical_relief(1.0, 0.5, 0.0) - 0.5) < 1e-12)
check("...no coverage, no relief; and relief never exceeds one", medical_relief(0.0, 0.5, 1.0) == 0.0
      and medical_relief(5.0, 0.5, 1.0) == 1.0)


# no medical node is a counter of war's kinds (data)
_medical_war_counters = [
    (node_id, counter["kind"]) for node_id, node in sorted(NODES.items()) if "medical" in node.get("traits", ())
    for counter in (node.get("mechanics") or {}).get("hazard_counters") or ()
    if counter["kind"] in ("output_factor", "sack_chance")]
check("diffused medicine gives no relief against output_factor or sack_chance: those are war's categories, not "
      "medicine's", not _medical_war_counters, _medical_war_counters)

_rome_gothic = _hazard("rome_100ad", "Adrianople and the Gothic settlement")
check("the Gothic settlement hazard itself still has no `condition` and no "
      "change to its `years` - the war still happens on the historical "
      "date; only what it costs moves, never whether or when",
      "condition" not in _rome_gothic and _rome_gothic["years"] == [376, 405],
      _rome_gothic)


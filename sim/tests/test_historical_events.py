"""historical_events: split verbatim from the old test_regressions.py (original lines 6644-6721).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# HISTORICAL EVENTS ANSWER TO WHAT WAS ACTUALLY BUILT: a dated hazard whose
# civilization file gives it a `condition` must fire as written, fire
# altered, or be averted depending on live player state - and the player
# must be told which, in every case. Political/religious/administrative
# hazards carry no `condition` at all and are untouched by any of this (see
# the civilization files' own reasoning); these are the ones that do.
def _hazard(civname, hazard_name):
    _c = S.load_civ(civname)
    return next(h for h in _c["hazards"] if h["name"] == hazard_name)


_rome_crossing = _hazard("rome_100ad", "The crossings, and the sack of Rome")
_s_unmet = sim(civ="rome_100ad")
_h_unmet = _s_unmet._resolve_hazard_condition(dict(_rome_crossing), 406, 406)
check("Rome, dependent on the African grain fleet: the grain crisis of 439 "
      "fires exactly as written",
      _h_unmet.get("output_factor") == _rome_crossing["output_factor"]
      and "grain fleet, so when Geiseric" in _s_unmet.log[0][1],
      _s_unmet.log)
_s_met = sim(civ="rome_100ad")
run_it(_s_met, "endowment_land", "crop_rotation")
_h_met = _s_met._resolve_hazard_condition(dict(_rome_crossing), 406, 406)
check("...but a household that already feeds itself has its output_factor "
      "hit from THIS hazard averted, told with the real cause, and its "
      "sack risk and staff loss left alone",
      "output_factor" not in _h_met
      and "sack_chance" in _h_met and "staff_loss" in _h_met
      and "never ate off that fleet" in _s_met.log[0][1],
      _h_met)

_rome_arab = _hazard("rome_100ad", "The Arab conquests close the Mediterranean")
_s_met2 = sim(civ="rome_100ad")
run_it(_s_met2, "endowment_land", "water_power_scale", "civ_road_paved")
_h_met2 = _s_met2._resolve_hazard_condition(dict(_rome_arab), 634, 634)
check("a household with its own land, power and roads is untouched when "
      "the Mediterranean closes, and the society's commerce values field "
      "is UNCHANGED by this (political attitude, not household ledger)",
      "output_factor" not in _h_met2 and "values" in _h_met2
      and _h_met2["values"] == _rome_arab["values"],
      _h_met2)

_en_dearth = _hazard("england_1300", "The dearth of the 1590s")
_s_en_met = sim(civ="england_1300")
run_it(_s_en_met, "crop_rotation", "ag2_silage_silo")
_h_en_met = _s_en_met._resolve_hazard_condition(dict(_en_dearth), 1594, 1594)
check("resilient farming averts the weather-driven 1590s dearth entirely",
      "staff_loss" not in _h_en_met, _h_en_met)
_s_en_unmet = sim(civ="england_1300")
_h_en_unmet = _s_en_unmet._resolve_hazard_condition(dict(_en_dearth), 1594, 1594)
check("...and without it, four failed harvests cost what they always did",
      _h_en_unmet.get("staff_loss") == _en_dearth["staff_loss"],
      _h_en_unmet)

_en_fire = _hazard("england_1300", "The Great Fire of London")
_s_fp = sim(civ="england_1300")
run_it(_s_fp, "civ_fireproofing")
_h_fp = _s_fp._resolve_hazard_condition(dict(_en_fire), 1666, 1666)
check("fireproof construction averts the Great Fire's sack risk for a "
      "household already built in brick and stone",
      "sack_chance" not in _h_fp, _h_fp)

_mx_war = _hazard("mexica_1500", "The wars of independence")
_s_mx_met = sim(civ="mexica_1500")
run_it(_s_mx_met, "met_mine_pumping")
_h_mx_met = _s_mx_met._resolve_hazard_condition(dict(_mx_war), 1810, 1810)
_mx_floor_met = 1.0 - (1.0 - _mx_war["output_factor"]) * 0.5
check("a household with its own mine pumps is ALTERED, not fully spared, "
      "by the wars of independence - the war itself still runs",
      abs(_h_mx_met["output_factor"] - _mx_floor_met) < 1e-9
      and "sack_chance" in _h_mx_met,
      _h_mx_met)

check("a hazard with no `condition` at all - Diocletian's reforms, the "
      "purely political case - is untouched by any of this machinery",
      "condition" not in _hazard("rome_100ad",
                                 "Diocletian's reforms and the Price Edict"),
      "ok")

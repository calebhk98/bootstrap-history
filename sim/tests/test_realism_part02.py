"""Regression coverage for combined tech-tree realism review, part 02."""
from .harness import *  # noqa: F401,F403


_GATES = {
 "tx2_paperclip": {"mfg_wire_drawing", "mt2_spring_steel", "mat_paper"},
 "hom_safety_pin": {"mfg_wire_drawing", "mt2_spring_steel", "cap_tol_100um"},
 "tx2_flyer": {"tex_spinning_wheel"}, "tx2_drawing_pin": {"mfg_wire_drawing", "mat_paper"},
 "tx2_spectacle_frame": {"hom_spectacles"},
 "tx2_pattern_grading": {"tx2_sizing_systems", "tex_pattern_cutting"},
 "com_optical_codebook": {"tr_semaphore_signal"}, "air_compass_magnetic": {"sea_lodestone"},
 "ag2_guano": {"ag2_guano_deposit_access"}, "ag2_hopping": {"ag2_malting"},
 "hom_flush_toilet_trap": {"hom_latrine_water_trap"},
 "prn_wire_mould_deckle": {"prn_hand_papermaking"},
 "tr_sleeper_ballast": {"tr_wooden_waggonway"},
 "mt2_pelletising": {"met_ore_crushing_sorting", "cap_heat_1100"},
 "sc2_institution_doctorate": {"fin_university", "sc2_institution_examination"},
 "sc2_institution_referee": {"sc2_institution_research_group", "sc2_institution_textbook"},
 "sc2_institution_research_group": {"school_founded"},
 "sc2_probability_axioms": {"arithmetic_positional", "algebra_symbolic"},
 "tr_hopper_wagon": {"tr_wooden_waggonway", "tr_sleeper_ballast"},
 "sc2_notation_decimal_point": {"sc2_notation_positional"},
 "sc2_notation_roots": {"algebra_symbolic"},
 "sc2_notation_exponents": {"algebra_symbolic"},
 "hom_sprung_mattress": {"mfg_wire_drawing", "tl_coil_spring", "mt2_spring_steel"},
 "sc2_institution_examination": {"school_founded", "sc2_institution_curriculum"},
 "sea_sternpost_rudder": {"sea_skeleton_first"},
 "mt2_type_metal": {"mat_antimony", "prn_type_punch"},
 "fud_whaling_industry": {"fud_whaling_gear", "sea_coastal_pilotage"},
}
_missing = {i: sorted(required - set(NODES[i]["pre"])) for i, required in _GATES.items()
            if not required <= set(NODES[i]["pre"])}
check("all part 02 hard gates have their causal prerequisites", not _missing, _missing)

_SUPPORT = {"tx2_cashmere_goat_stock", "tx2_jute_seed_stock", "tx2_angora_goat_stock",
            "ag2_guano_deposit_access",
            "ag2_hop_stock", "ag2_pyrethrum_stock", "fud_whaling_gear", "lnd_whippletree",
            "lnd_nailed_horseshoe", "mat_antimony"}
check("silk and ramie fibre need the living stock held, not a research node standing for it",
      "silkworm_eggs_kg" in NODES["tx2_silk_fibre"]["holds"] and "ramie_stock_kg" in NODES["tx2_ramie_fibre"]["holds"],
      None)
check("cashmere, mohair, jute, hops and pyrethrum need the stock held, not a research node standing for it",
      all(material in NODES[node_id]["holds"] for node_id, material in (
          ("tx2_cashmere", "cashmere_goat_kg"), ("tx2_mohair", "angora_goat_kg"),
          ("tx2_jute_fibre", "jute_seed_kg"), ("ag2_hopping", "hop_rhizome_kg"),
          ("ag2_pyrethrum", "pyrethrum_stock_kg"))), None)
check("all part 02 supporting acquisition and split nodes exist",
      _SUPPORT <= set(NODES), sorted(_SUPPORT - set(NODES)))
check("the collar, whippletree, and horseshoe are independent nodes",
      NODES["horse_collar"]["name"] == "Rigid padded horse collar"
      and NODES["lnd_whippletree"]["pre"] == ["horse_collar"]
      and "horse_collar" not in NODES["lnd_nailed_horseshoe"]["pre"],
      {i: NODES[i]["pre"] for i in ("horse_collar", "lnd_whippletree", "lnd_nailed_horseshoe")})

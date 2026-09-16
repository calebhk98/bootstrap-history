"""Regression coverage for combined tech-tree realism review, part 02."""
from .harness import *  # noqa: F401,F403


_ROMAN = set("""tx2_warp_sizing med_bone_setting tx2_heddle tx2_wool_fibre tx2_beam fin_employment_contract tx2_pin med_amputation tx2_comb tx2_currying fin_apprenticeship med_obstetric_practice fin_seigniorage fin_usury_law fin_arbitrage fin_bankruptcy fin_tariff fin_monopoly fin_bimetallism fin_mortgage met_ore_crushing_sorting hom_toys_dolls tx2_doll hom_umbrella cn_gypsum_plaster pwr_petroleum_seeps tx2_needle sea_lodestone tx2_eye_pointed_needle ag2_marling tex_mordanting cn_stone_polish ag2_liming ag2_composting ag2_potash civ_gate_sluice tex_indigo tr_reefing mfg_flux mat_obsidian_blade mfg_enamelling mfg_adhesive_bond mfg_hot_riveting mfg_cold_riveting mt2_timbering_safety mfg_painting mt2_earthenware tr_block_tackle fud_hay_making_storage cn_post_lintel mfg_soft_solder ag2_malting ag2_oil_pressing pwr_coal_seam civ_town_planning ag2_refrigeration_ice cn_pile_driving fud_fish_curing_and_smoking mat_papyrus civ_street_paved mat_parchment med_herbal_pharmacy tx2_scouring tx2_dyeing_fibre tx2_dyeing_yarn tx2_dyeing_piece tx2_alum_tanning tr_square_rig fin_pawnshop tx2_bottle tx2_asbestos_cloth met_bloomery_bog_iron sea_lead_sheathing sc2_institution_textbook fin_trading_post fin_ferry fin_gambling_house fin_census""".split())
_rome = sim(civ="rome_100ad")
check("part 02's 78 Roman technologies are explicit opening grants",
      _ROMAN <= _rome.granted, sorted(_ROMAN - _rome.granted))
_ROME_ONLY = _ROMAN - {"mat_obsidian_blade"}  # Independently inherited by the Mexica.
check("part 02's Rome-only grants are not ambient Mexica knowledge",
      not (_ROME_ONLY & sim(civ="mexica_1500").granted),
      sorted(_ROME_ONLY & sim(civ="mexica_1500").granted))

_GATES = {
 "tx2_cashmere": {"tx2_cashmere_goat_stock"}, "tx2_jute_fibre": {"tx2_jute_seed_stock"},
 "tx2_mohair": {"tx2_angora_goat_stock"}, "tx2_ramie_fibre": {"tx2_ramie_plant_stock"},
 "tx2_paperclip": {"mfg_wire_drawing", "mt2_spring_steel", "mat_paper"},
 "hom_safety_pin": {"mfg_wire_drawing", "mt2_spring_steel", "cap_tol_100um"},
 "tx2_flyer": {"tex_spinning_wheel"}, "tx2_drawing_pin": {"mfg_wire_drawing", "mat_paper"},
 "tx2_spectacle_frame": {"hom_spectacles"},
 "tx2_pattern_grading": {"tx2_sizing_systems", "tex_pattern_cutting"},
 "com_optical_codebook": {"tr_semaphore_signal"}, "air_compass_magnetic": {"sea_lodestone"},
 "ag2_guano": {"ag2_guano_deposit_access"}, "ag2_hopping": {"ag2_hop_stock", "ag2_malting"},
 "hom_flush_toilet_trap": {"hom_latrine_water_trap"},
 "prn_wire_mould_deckle": {"prn_hand_papermaking"},
 "tr_sleeper_ballast": {"tr_wooden_waggonway"},
 "mt2_pelletising": {"met_ore_crushing_sorting", "cap_heat_1100"},
 "sc2_institution_doctorate": {"fin_university", "sc2_institution_examination"},
 "sc2_institution_referee": {"sc2_institution_research_group", "sc2_institution_textbook"},
 "sc2_institution_research_group": {"school_founded", "sc2_institution_funded_programme"},
 "sc2_probability_axioms": {"arithmetic_positional", "algebra_symbolic"},
 "tr_hopper_wagon": {"tr_wooden_waggonway", "tr_sleeper_ballast"},
 "sc2_notation_decimal_point": {"sc2_notation_positional"},
 "sc2_notation_roots": {"algebra_symbolic"}, "ag2_pyrethrum": {"ag2_pyrethrum_stock"},
 "sc2_notation_exponents": {"algebra_symbolic"},
 "hom_sprung_mattress": {"mfg_wire_drawing", "tl_coil_spring", "mt2_spring_steel"},
 "tx2_silk_fibre": {"tx2_silkworm_stock"},
 "sc2_institution_examination": {"school_founded", "sc2_institution_curriculum"},
 "sea_sternpost_rudder": {"sea_skeleton_first"},
 "mt2_type_metal": {"mat_antimony", "prn_type_punch"},
 "fud_whaling_industry": {"fud_whaling_gear", "sea_coastal_pilotage"},
}
_missing = {i: sorted(required - set(NODES[i]["pre"])) for i, required in _GATES.items()
            if not required <= set(NODES[i]["pre"])}
check("all 33 part 02 hard gates have their causal prerequisites", not _missing, _missing)

_SUPPORT = {"tx2_cashmere_goat_stock", "tx2_jute_seed_stock", "tx2_angora_goat_stock",
            "tx2_ramie_plant_stock", "tx2_silkworm_stock", "ag2_guano_deposit_access",
            "ag2_hop_stock", "ag2_pyrethrum_stock", "fud_whaling_gear", "lnd_whippletree",
            "lnd_nailed_horseshoe", "mat_antimony"}
check("all part 02 supporting acquisition and split nodes exist",
      _SUPPORT <= set(NODES), sorted(_SUPPORT - set(NODES)))
check("the collar, whippletree, and horseshoe are independent nodes",
      NODES["horse_collar"]["name"] == "Rigid padded horse collar"
      and NODES["lnd_whippletree"]["pre"] == ["horse_collar"]
      and "horse_collar" not in NODES["lnd_nailed_horseshoe"]["pre"],
      {i: NODES[i]["pre"] for i in ("horse_collar", "lnd_whippletree", "lnd_nailed_horseshoe")})

"""Regression coverage for combined tech-tree realism review, part 05."""
from .harness import *  # noqa: F401,F403


_england = sim(civ="england_1300")
_ENGLISH_KNOWN = set("""mat_papyrus mat_parchment med_amputation med_bone_setting
med_herbal_pharmacy med_obstetric_practice met_bloomery_bog_iron
met_ore_crushing_sorting mfg_adhesive_bond mfg_cold_riveting mfg_enamelling
mfg_flux mfg_hot_riveting mfg_painting mfg_soft_solder mt2_amalgamation
mt2_earthenware mt2_timbering_safety pwr_coal_seam pwr_petroleum_seeps
sc2_institution_textbook sea_lead_sheathing sea_lodestone tex_indigo
tex_mordanting tr_block_tackle tr_reefing tr_square_rig tx2_alum_tanning
 tx2_asbestos_cloth tx2_beam tx2_bleaching_sun tx2_bottle tx2_comb tx2_currying
 tx2_doll tx2_dyeing_fibre tx2_dyeing_piece tx2_dyeing_yarn tx2_eye_pointed_needle
 tx2_flax_fibre tx2_heddle tx2_hemp_fibre tx2_needle tx2_pin tx2_retting
 tx2_rope_lay tx2_scouring tx2_selvedge tx2_shed tx2_warp_sizing
 tx2_wool_fibre""".split())
check("all 52 part 05 practices judged known in England by 1300 are grants",
      _ENGLISH_KNOWN <= _england.granted, sorted(_ENGLISH_KNOWN - _england.granted))
check("English paper access still does not imply domestic rag-paper production",
      "mat_paper" in _england.granted and "rag_paper" not in _england.granted,
      sorted({"mat_paper", "rag_paper"} & _england.granted))
check("part 05's contaminated English papermaking descendants are not inherited",
      not ({"prn_hand_papermaking", "prn_pulp_stamper", "prn_sizing_surface"}
           & _england.granted), sorted(_england.granted))

_mexica = sim(civ="mexica_1500")
_MEXICA_SEEDS = {"fud_chinampa", "fud_maize", "fud_cacao",
                 "civ_monumental_stone", "mat_obsidian_blade"}
check("part 05's five explicit Mexica seeds remain intact",
      _MEXICA_SEEDS <= _mexica.granted, sorted(_MEXICA_SEEDS - _mexica.granted))
_MEXICA_CONTAMINANTS = set("""civ_glass_windows civ_iron_wrought civ_marble_facing
fin_coined_money fin_maritime_loan hom_candle_tallow hom_flush_latrine_simple
hom_hypocaust hom_lead_plumbing hom_perfume_enfleurage hom_public_bath
lnd_axle_pivot_front lnd_milestone lnd_paved_road_network lnd_tyre_iron
lnd_wheel_spoked mat_asbestos mat_brass mat_calamine mat_glass_soda mat_lead
mat_linen mat_mercury mat_natron mat_olive_oil mat_shellac mat_silk mat_tallow
mat_tin mat_vitriols mat_wrought_iron med_cataract_couching med_legal_physician
med_opium_mandrake med_surgical_kit_good opt_burning_glass opt_dioptra
opt_geared_mechanisms opt_groma opt_water_globe_magnifier prn_mosaic_fresco
prn_papyrus_sheets prn_parchment_sheets prn_theatre_pantomime pwr_force_pump
pwr_screw_press_power sea_sounding_lines tex_dye_madder tex_dye_murex
tex_dye_woad tex_sailcloth tex_silk_trade tex_two_beam_loom
tex_warp_weighted_loom""".split())
check("all definite Old World Mexica contaminants in part 05 are excluded",
      not (_MEXICA_CONTAMINANTS & _mexica.granted),
      sorted(_MEXICA_CONTAMINANTS & _mexica.granted))
check("human power no longer smuggles draught animals into the Mexica start",
      "cap_power_human" in _mexica.granted and "cap_power_muscle" not in _mexica.granted
      and NODES["cap_power_muscle"]["pre"] == ["cap_power_human"],
      sorted({"cap_power_human", "cap_power_muscle"} & _mexica.granted))
check("human mechanisms and animal machines use distinct capability gates",
      NODES["cn_crane_treadwheel"]["pre"][0] == "cap_power_human"
      and "cap_power_muscle" in NODES["en_horse_gin"]["pre"]
      and "cap_power_muscle" in NODES["pwr_animal_treadmill"]["pre"],
      {i: NODES[i]["pre"] for i in
       ("cn_crane_treadwheel", "en_horse_gin", "pwr_animal_treadmill")})
for _civ in ("rome_100ad", "han_china_100ad", "norse_900ad", "england_1300",
             "mexica_1500"):
    check("%s explicitly has universal human power" % _civ,
          "cap_power_human" in sim(civ=_civ).granted, _civ)

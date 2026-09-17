"""Regression coverage for combined tech-tree realism review, part 04."""
from .harness import *  # noqa: F401,F403


_norse = sim(civ="norse_900ad")
_NORSE_WRONG = {
    "med_cataract_couching", "med_legal_physician", "med_opium_mandrake",
    "med_surgical_kit_good", "opt_dioptra", "opt_geared_mechanisms", "opt_groma",
    "prn_mosaic_fresco", "prn_papyrus_sheets", "prn_theatre_pantomime",
    "sea_monsoon_route", "sea_mortise_tenon", "sea_spritsail", "tex_dye_murex",
}
check("part 04's foreign Norse inheritance is excluded",
      not (_NORSE_WRONG & _norse.granted), sorted(_NORSE_WRONG & _norse.granted))
_NORSE_LOCAL = set("""ag2_composting ag2_liming ag2_malting ag2_marling ag2_oil_pressing
ag2_potash ag2_refrigeration_ice cn_gypsum_plaster cn_pile_driving cn_post_lintel
cn_stone_polish fin_ferry fin_gambling_house fin_inn fin_trading_post
fud_fish_curing_and_smoking fud_hay_making_storage mat_obsidian_blade mat_parchment
med_obstetric_practice met_ore_crushing_sorting mfg_cold_riveting mfg_flux
mfg_hot_riveting mfg_painting mfg_soft_solder mt2_earthenware mt2_timbering_safety
tex_mordanting tr_block_tackle tr_reefing tr_square_rig tx2_alum_tanning tx2_beam
 tx2_bleaching_sun tx2_bottle tx2_comb tx2_currying tx2_doll tx2_dyeing_fibre
 tx2_dyeing_piece tx2_dyeing_yarn tx2_eye_pointed_needle tx2_flax_fibre tx2_heddle
 tx2_hemp_fibre tx2_needle tx2_pin tx2_retting tx2_rope_lay tx2_scouring tx2_selvedge
 tx2_shed tx2_warp_sizing tx2_wool_fibre""".split())
check("part 04's defensible Norse local practices are explicit grants",
      _NORSE_LOCAL <= _norse.granted, sorted(_NORSE_LOCAL - _norse.granted))
_NORSE_NOT_LOCAL = {
    "fin_apprenticeship", "fin_employment_contract", "fin_hotel", "fin_pawnshop",
    "hom_umbrella", "mat_papyrus", "med_herbal_pharmacy", "mt2_amalgamation",
    "sc2_institution_textbook", "sea_lead_sheathing", "sea_lodestone", "tex_indigo",
}
check("ambiguous part 04 Norse CHECK rows are not promoted to local inheritance",
      not (_NORSE_NOT_LOCAL & _norse.granted), sorted(_NORSE_NOT_LOCAL & _norse.granted))

_england = sim(civ="england_1300")
_ENGLISH_WRONG = {
    "clock_pendulum", "crank_conrod", "hom_hypocaust", "hom_public_bath",
    "prn_papyrus_sheets", "rag_paper", "sea_monsoon_route", "sea_mortise_tenon",
    "sea_spritsail", "tex_dye_murex",
}
check("part 04's anachronistic or bundled English inheritance is excluded",
      not (_ENGLISH_WRONG & _england.granted), sorted(_ENGLISH_WRONG & _england.granted))
_ENGLISH_KNOWN = set("""ag2_composting ag2_liming ag2_malting ag2_marling ag2_oil_pressing
ag2_potash ag2_refrigeration_ice cn_gypsum_plaster cn_pile_driving cn_post_lintel
cn_stone_polish fin_apprenticeship fin_arbitrage fin_bankruptcy fin_bimetallism
fin_census fin_employment_contract fin_ferry fin_gambling_house fin_hotel fin_inn
fin_monopoly fin_mortgage fin_pawnshop fin_plantation fin_seigniorage fin_tariff
fin_trading_post fin_usury_law fud_fish_curing_and_smoking fud_hay_making_storage
hom_toys_dolls hom_umbrella mat_obsidian_blade clock_mechanical_escapement""".split())
check("all part 04 practices judged known in England by 1300 are explicit grants",
      _ENGLISH_KNOWN <= _england.granted, sorted(_ENGLISH_KNOWN - _england.granted))
check("medieval clockwork is split from pendulum timekeeping",
      NODES["clock_pendulum"]["pre"][0] == "clock_mechanical_escapement"
      and "pendulum" not in NODES["clock_mechanical_escapement"]["name"].lower(),
      NODES["clock_pendulum"]["pre"])
check("the inherited watermill node no longer claims general line shafting",
      "line shaft" not in NODES["water_power_scale"]["name"].lower()
      and "not included" in NODES["water_power_scale"]["note"],
      NODES["water_power_scale"]["note"])

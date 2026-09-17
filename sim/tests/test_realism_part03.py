"""Regression coverage for combined tech-tree realism review, part 03."""
from .harness import *  # noqa: F401,F403


_rome = sim(civ="rome_100ad")
_ROMAN = {
    "civ_circus_racecourse", "fin_inn", "fin_hotel",
    "mt2_amalgamation", "fin_plantation",
}
check("part 03's inherited Roman practices and circus are explicit grants",
      _ROMAN <= _rome.granted, sorted(_ROMAN - _rome.granted))

_GATES = {
    "fin_marine_insurance": {"fin_maritime_loan", "fin_contract_law", "fin_argentarii"},
    "fin_postal_service": {"fin_contract_law", "lnd_cursus_publicus", "fin_inn"},
    "mt2_solder_lead_tin": {"mfg_soft_solder", "mat_lead", "mat_tin", "units_standards"},
    "fin_racecourse": {"civ_circus_racecourse", "fin_argentarii"},
    "fin_theatre_business": {"prn_theatre_pantomime", "fin_contract_law"},
    "tx2_watch_case": {"hom_pocket_watch"},
}
_missing = {node: sorted(required - set(NODES[node]["pre"]))
            for node, required in _GATES.items()
            if not required <= set(NODES[node]["pre"])}
check("all six actionable part 03 Roman model findings have causal gates",
      not _missing, _missing)
check("race and theatre ventures no longer confuse their venues with an amphitheatre",
      "civ_amphitheatre" not in NODES["fin_racecourse"]["pre"]
      and "civ_amphitheatre" not in NODES["fin_theatre_business"]["pre"],
      {node: NODES[node]["pre"] for node in ("fin_racecourse", "fin_theatre_business")})
check("the solder node gives the correct eutectic composition",
      "61.9% tin" in NODES["mt2_solder_lead_tin"]["note"]
      and "50-50" not in NODES["mt2_solder_lead_tin"]["note"],
      NODES["mt2_solder_lead_tin"]["note"])

_han = sim(civ="han_china_100ad")
_HAN_BAD = {
    "civ_glass_windows", "civ_marble_facing", "crank_conrod", "hom_hypocaust",
    "hom_lead_plumbing", "hom_perfume_enfleurage", "hom_public_bath", "horse_collar",
    "med_legal_physician", "opt_groma", "prn_mosaic_fresco", "prn_papyrus_sheets",
    "prn_parchment_sheets", "prn_theatre_pantomime", "rag_paper",
    "sea_magnetic_compass", "sea_mortise_tenon", "sea_spritsail", "tex_dye_murex",
}
check("part 03's foreign or overbundled Han grants remain excluded",
      not (_HAN_BAD & _han.granted), sorted(_HAN_BAD & _han.granted))
check("Han retains paper material and lodestone knowledge without mature bundled processes",
      {"mat_paper", "sea_lodestone"} <= _han.granted,
      sorted({"mat_paper", "sea_lodestone"} - _han.granted))

_norse = sim(civ="norse_900ad")
_NORSE_BAD_IN_PART03 = {
    "civ_glass_windows", "civ_marble_facing", "fin_government", "fin_tax_farming",
    "hom_flush_latrine_simple", "hom_hypocaust", "hom_lead_plumbing",
    "hom_perfume_enfleurage", "hom_public_bath",
}
check("part 03's foreign Norse grants remain excluded",
      not (_NORSE_BAD_IN_PART03 & _norse.granted),
      sorted(_NORSE_BAD_IN_PART03 & _norse.granted))

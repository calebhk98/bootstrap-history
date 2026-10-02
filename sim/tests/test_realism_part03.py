"""Regression coverage for combined tech-tree realism review, part 03."""
from .harness import *  # noqa: F401,F403


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



"""`validate` rejects a pathogen file (data/disease/) with a missing source tag, a bad stage or an out-of-range
reproduction number, and a node's `disease_effects` or a civilisation's `disease_exposure` that names a pathogen
with no file or an effect the disease step does not read."""
from typing import List

from sim.disease import api as disease
from sim.geography.api import endemic_problems, modes_carrying, open_map

EFFECT_TARGETS = ("case_fatality", "transmission")


def check_disease_data(nodes=None, civilisations=None) -> List[str]:
    problems = disease.check_pathogen_data() + endemic_problems()
    known = set(disease.pathogen_ids())
    world_map = open_map()
    modes = set(modes_carrying("goods")) | set(modes_carrying("living_stock"))
    for node_id, node in sorted((nodes or {}).items()):
        spec = (node.get("mechanics") or {}).get("disease_effects")
        if spec is None:
            continue
        if spec.get("acts_on") not in EFFECT_TARGETS:
            problems.append("%s: disease_effects.acts_on must be one of %s" % (node_id, ", ".join(EFFECT_TARGETS)))
        if not isinstance(spec.get("factor"), (int, float)) or not 0.0 <= spec["factor"] <= 1.0:
            problems.append("%s: disease_effects.factor must be a multiplier between 0 and 1" % node_id)
        problems += ["%s: disease_effects names pathogen %s, which has no file in data/disease/" % (node_id, name)
                     for name in spec.get("pathogens") or () if name not in known]
    for civ_id, civ in sorted((civilisations or {}).items()):
        for entry in (civ.get("disease_exposure") or {}).get("outside_contact", ()):
            problems += ["%s: disease_exposure names pathogen %s, which has no file in data/disease/" % (civ_id, name)
                         for name in entry.get("pathogens", ()) if name not in known]
            years = entry.get("years")
            if years is not None and not (isinstance(years, list) and len(years) == 2 and years[0] <= years[1]):
                problems.append("%s: disease_exposure.outside_contact years must be [first, last]" % civ_id)
            if not entry.get("tiles"):
                problems.append("%s: disease_exposure.outside_contact needs the map tiles the pathogens live on" % civ_id)
            problems += ["%s: disease_exposure names tile %s, which is not on the map" % (civ_id, tile)
                         for tile in entry.get("tiles", ()) if tile not in world_map.tiles]
            problems += ["%s: disease_exposure names carrier mode %s, which is not a route mode" % (civ_id, mode)
                         for mode in entry.get("carrier_modes", ()) if mode not in modes]
    return problems

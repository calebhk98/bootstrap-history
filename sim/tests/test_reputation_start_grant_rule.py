"""Who a society is granted at the start: the opening grant is exactly the civilisation's declared starting techs
(`declared_starting_techs`), so Han China is not handed Rome's courier relay or Ptolemy's lighthouse, the Mexica are not
handed other people's seas, and a seafaring society keeps its own. Read on the civilisation record and the tree, no game is
built. The tree data checks are test_reputation."""
from .harness import *  # noqa: F401,F403

from sim.engine.data import load_civ
from sim.knowledge.api import declared_starting_techs

QUICK_TOPIC = True


def _granted(civ_id):
    granted = set(declared_starting_techs(load_civ(civ_id), NODES))
    check("%s opens with something granted" % civ_id, bool(granted))
    return granted


_han = _granted("han_china_100ad")
check("Han China is never handed Rome's courier relay or Ptolemy's lighthouse for free",
      "lnd_cursus_publicus" not in _han
      and "sea_pharos_lighthouse" not in _han,
      (sorted(_han & {"lnd_cursus_publicus", "sea_pharos_lighthouse"})))

_mex = _granted("mexica_1500")
check("the Mexica are not handed other people's seas: no sail, no Mediterranean hull, no merchant fleet, no monsoon "
      "crossing, and canoe use does not silently grant an Old World nautical package",
      not any(tech_id in _mex for tech_id in
              ("sea_square_sail", "sea_spritsail", "sea_mortise_tenon", "sea_merchant_ships_large", "sea_monsoon_route",
               "sea_anchor", "sea_sounding_lines", "sea_coastal_pilotage", "sea_steering_oars")),
      sorted(tech_id for tech_id in _mex if tech_id.startswith("sea_")))
check("the ocean-going hull gate remains a buildable route, not an inherited gift",
      "exp_oceangoing_hull" not in _mex and "exp_oceangoing_hull" in NODES,
      sorted(x for x in PLANNER.closure(NODES, "exp_oceangoing_hull") if x.startswith("sea_")))
check("a seafaring society is untouched by the gate", "sea_square_sail" in _granted("norse_900ad"), True)

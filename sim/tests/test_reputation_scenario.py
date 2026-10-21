"""Who a society is granted at the start, through a game for each civilisation: Han China is not handed Rome's courier
relay or Ptolemy's lighthouse, the Mexica are not handed other people's seas, and a seafaring society is untouched by the
gate (the grant at the opening consults `needs_first`). The tree data checks are test_reputation."""
from .harness import *  # noqa: F401,F403

_han = sim(civ="han_china_100ad")
check("Han China is never handed Rome's courier relay or Ptolemy's lighthouse for free",
      "lnd_cursus_publicus" not in _han.granted
      and "sea_pharos_lighthouse" not in _han.granted,
      (sorted(_han.granted & {"lnd_cursus_publicus", "sea_pharos_lighthouse"})))

_mex = sim(civ="mexica_1500")
check("the Mexica are not handed other people's seas: no sail, no Mediterranean hull, no merchant fleet, no monsoon "
      "crossing, and canoe use does not silently grant an Old World nautical package",
      not any(tech_id in _mex.granted for tech_id in
              ("sea_square_sail", "sea_spritsail", "sea_mortise_tenon", "sea_merchant_ships_large", "sea_monsoon_route",
               "sea_anchor", "sea_sounding_lines", "sea_coastal_pilotage", "sea_steering_oars")),
      sorted(tech_id for tech_id in _mex.granted if tech_id.startswith("sea_")))
check("the ocean-going hull gate remains a buildable route, not an inherited gift",
      "exp_oceangoing_hull" not in _mex.granted and "exp_oceangoing_hull" in NODES,
      sorted(x for x in PLANNER.closure(NODES, "exp_oceangoing_hull") if x.startswith("sea_")))
check("a seafaring society is untouched by the gate", "sea_square_sail" in sim(civ="norse_900ad").granted, True)

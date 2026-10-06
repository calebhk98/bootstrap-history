"""Opening knowledge is exactly what the civilisation declares, and nothing else."""
from .harness import *  # noqa: F401,F403

# The two civilisations with the least in common stand for the rest; the free-on-turn-one
# check for every civilisation lives in test_civilisation_data_integrity.
for _civ in ("rome_100ad", "mexica_1500"):
    _start = sim(civ=_civ)
    _declared = set(S.load_civ(_civ)["starting_techs"])
    check("%s holds exactly its declared starting technologies" % _civ,
          _start.granted == _declared and _start.done == _declared,
          sorted((_start.granted ^ _declared) | (_start.done ^ _declared)))

# A typo in explicit scenario data must fail fast, not degrade into a
# different opening state.
_bad_civ = copy.deepcopy(S.load_civ("rome_100ad"))
_bad_civ["starting_techs"].append("not_a_real_node")
try:
    S.Sim(NODES, ORDER, random.Random(1), events=False, civ=_bad_civ)
except ValueError as _error:
    _rejected_unknown_start = "not_a_real_node" in str(_error)
else:
    _rejected_unknown_start = False
check("unknown explicit starting technologies fail fast",
      _rejected_unknown_start, "invalid id was accepted")

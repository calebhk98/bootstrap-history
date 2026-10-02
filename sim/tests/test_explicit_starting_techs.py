"""Opening knowledge is exactly what the civilisation declares, and nothing else."""
from .harness import *  # noqa: F401,F403

_civilisation_ids = S.civilization_ids()
_starts = {civ_id: sim(civ=civ_id) for civ_id in _civilisation_ids}

for _civ, _start in _starts.items():
    _declared = set(S.load_civ(_civ)["starting_techs"])
    check("%s holds exactly its declared starting technologies" % _civ,
          _start.granted == _declared and _start.done == _declared,
          sorted((_start.granted ^ _declared) | (_start.done ^ _declared)))

# Ownership must stay stable after time advances; zero-cost descendants are
# projects, not a delayed ambient gift.
for _civ, _start in _starts.items():
    _before = set(_start.granted)
    _start.step()
    check("%s: advancing time does not infer additional starting ownership" % _civ,
          _start.granted == _before, sorted(_start.granted ^ _before))

# A typo in explicit scenario data must fail fast, not degrade into a
# different opening state.
_bad_civ = copy.deepcopy(S.load_civ(_civilisation_ids[0]))
_bad_civ["starting_techs"].append("not_a_real_node")
try:
    S.Sim(NODES, ORDER, random.Random(1), events=False, civ=_bad_civ)
except ValueError as _error:
    _rejected_unknown_start = "not_a_real_node" in str(_error)
else:
    _rejected_unknown_start = False
check("unknown explicit starting technologies fail fast",
      _rejected_unknown_start, "invalid id was accepted")

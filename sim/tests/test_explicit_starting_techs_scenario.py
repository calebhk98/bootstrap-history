"""Scenario: a game opens holding exactly the starting technologies its civilisation declares, and nothing else. The
declared set and the refusal of an unknown technology are in test_explicit_starting_techs."""
from .harness import *  # noqa: F401,F403

# One civilisation stands for the rest; the free-on-turn-one
# check for every civilisation lives in test_civilisation_data_integrity.
for _civ in ("rome_100ad",):
    _start = unopened_sim(civ=_civ)
    _declared = set(S.load_civ(_civ)["starting_techs"])
    check("%s holds exactly its declared starting technologies" % _civ,
          _start.granted == _declared and _start.done == _declared,
          sorted((_start.granted ^ _declared) | (_start.done ^ _declared)))

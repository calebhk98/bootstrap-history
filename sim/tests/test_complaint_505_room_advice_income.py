"""Complaint 505: the room advice states the places a node adds at the household's
present income, the same figure household_room() moves by once it is open."""
from .harness import *  # noqa: F401,F403

_STAFF_ONLY_NODES = ("freedman_staff", "paid_apprentice_staff")


def _advertised_and_actual(capital, node_id):
    before = unopened_sim(capital=capital)
    flat = dict(before.ROOM_SOURCES)[node_id]
    advertised = before.labour.room_added_by(flat)
    room_before = before.labour.household_room()
    opened = run_it(unopened_sim(capital=capital), node_id)
    return flat, advertised, opened.labour.household_room() - room_before


for _capital in (20000.0, 2000000.0):
    for _node_id in _STAFF_ONLY_NODES:
        _flat, _advertised, _actual = _advertised_and_actual(_capital, _node_id)
        check("%s advertises the places it adds at capital %.0f" % (_node_id, _capital),
              abs(_advertised - _actual) < 0.05, (_flat, _advertised, _actual))

_thin_flat, _thin_advertised, _ = _advertised_and_actual(20000.0, "freedman_staff")
_rich_flat, _rich_advertised, _ = _advertised_and_actual(2000000.0, "freedman_staff")
check("a thin purse is promised less than the flat figure, a richer one more",
      _thin_advertised < _rich_advertised < _rich_flat, (_thin_advertised, _rich_advertised, _rich_flat))

_advice = unopened_sim(capital=20000.0).labour._room_advice()
check("the advice does not print the flat figure for a node at a thin income",
      "freedman_staff (+%d places)" % _thin_flat not in _advice, _advice)
check("...and says the places grow with surplus", "grow with surplus" in _advice, _advice)

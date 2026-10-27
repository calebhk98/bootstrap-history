"""Complaint 640 (from the craftsmen wording scenario): the people a founder can oversee are the person's own share, the deputies,
the worker housing and the switched-on effects, and the breakdown rows add up to exactly that total whatever the household holds.
`supervision_room` and `supervision_room_from` are called on a stand-in labour over a stub world."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.labour.labour_capacity import CapacityMixin

PARTNERSHIP = ("fin_societas", {"flat": 4.0, "words": "a legally recognised partnership", "gate": "has"})
BRANCHES = ("fin_chain_store", {"per_unit": 2.5, "words": "branches in other towns"})


class Labour(CapacityMixin):
    """Only what the supervision rules read: the household, and the effects that hold."""

    def __init__(self, directors_extra=0.0, housing=0.0, held=(), units=1.0):
        terms = [PARTNERSHIP, BRANCHES]
        holds = lambda key, spec: key in held
        value = lambda key, spec: spec["flat"] if "flat" in spec else spec["per_unit"] * units
        self._world = SimpleNamespace(
            workforce=SimpleNamespace(directors_extra=directors_extra, worker_housing_places=housing),
            effect_terms=lambda channel: terms, effect_holds=holds, effect_value=value,
            effect_sum=lambda channel, start=0.0: start + sum(value(key, spec) for key, spec in terms if holds(key, spec)))


def total_of_rows(labour):
    return sum(row["people"] for row in labour.supervision_room_from())


bare = Labour()
check("a person alone oversees the declared share", bare.supervision_room() == CapacityMixin.SUPERVISION_ROOM_SELF, bare.supervision_room())
check("deputies add their declared share each", Labour(directors_extra=2.0).supervision_room()
      == CapacityMixin.SUPERVISION_ROOM_SELF + 2.0 * CapacityMixin.SUPERVISION_ROOM_PER_DIRECTOR_EXTRA, None)
check("worker housing adds its places", Labour(housing=5.0).supervision_room() == CapacityMixin.SUPERVISION_ROOM_SELF + 5.0, None)
check("a switched-on effect adds its value", Labour(held=("fin_societas",)).supervision_room()
      == CapacityMixin.SUPERVISION_ROOM_SELF + 4.0, None)
check("an effect that does not hold adds nothing", Labour(held=()).supervision_room() == CapacityMixin.SUPERVISION_ROOM_SELF, None)

rows = Labour(held=("fin_societas",)).supervision_room_from()
check("a held effect is named in the breakdown with what it is", any(row["source"] == "fin_societas" and row["people"] == 4.0
      and row["what_it_is"] == PARTNERSHIP[1]["words"] for row in rows), rows)
check("the breakdown always names the person's own share", rows[0]["source"] == "yourself", rows)

for label, labour in (("a bare household", Labour()), ("one with deputies", Labour(directors_extra=1.5)),
                      ("one with a partnership", Labour(held=("fin_societas",))),
                      ("one with branches by the unit", Labour(held=("fin_chain_store",), units=3.0)),
                      ("one with worker housing", Labour(housing=7.0)),
                      ("one with everything", Labour(directors_extra=1.5, housing=7.0, held=("fin_societas", "fin_chain_store"), units=3.0))):
    check("the breakdown adds up to the total for %s" % label, abs(total_of_rows(labour) - labour.supervision_room()) < 1e-9,
          (total_of_rows(labour), labour.supervision_room()))

"""Complaint 505: the room advice states the places a node adds at the household's present income, the same figure the
household's room moves by once the node is open. `room_added_by`, `staff_capacity` and `_room_advice` are called on a stand-in
for the labour world (Complaint 640: no game is built)."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_capacity import CapacityMixin
from sim.refusal import facts_of

FLAT_PLACES = 40.0
BASE_ARTISANS = 10.0
POPULATION_SCALE = 0.8
THIN_PURSE, RICH_PURSE = 15.0, 500.0   # people the spare income can pay


class StandInLabour(CapacityMixin):
    """Only what the room figures read: the load the running institutions carry, what the income can pay, the headroom."""

    def __init__(self, afford, artisans=BASE_ARTISANS, room_sources=(("freedman_staff", FLAT_PLACES),)):
        projects = types.SimpleNamespace(done=set(), operating=set())
        self._world = types.SimpleNamespace(
            household=types.SimpleNamespace(), projects=projects,
            ROOM_SOURCES=list(room_sources), nodes={node_id: {} for node_id, _places in room_sources},
            is_venture=lambda node_id: True, is_visible=lambda node_id: True,
            closure=lambda nodes, node_id: {node_id}, start_reason=lambda node_id, _why=True: (True, ""),
            money_text=lambda amount, grouped=False: "%g" % amount, housing_price_per_place=lambda: 100.0)
        self.afford, self.artisans = afford, artisans

    def _institutional_load(self, with_directors=False):
        return (0.0, self.artisans, 0.0) if with_directors else (0.0, self.artisans)

    def _staffing_affordability(self):
        return self.afford, POPULATION_SCALE

    def supervision_room(self):
        return 6.0


def actual_change(afford, places):
    """What the room (the ceiling on trained people) moves by once a source of `places` is running."""
    before = StandInLabour(afford).staff_capacity()[1]
    return StandInLabour(afford, artisans=BASE_ARTISANS + places).staff_capacity()[1] - before


class RoomAdviceStatesTheIncomeFigure(unittest.TestCase):
    def test_the_advertised_places_are_the_places_the_room_moves_by(self):
        for afford in (THIN_PURSE, RICH_PURSE):
            advertised = StandInLabour(afford).room_added_by(FLAT_PLACES)
            self.assertAlmostEqual(advertised, actual_change(afford, FLAT_PLACES), places=9, msg=afford)

    def test_a_thin_purse_is_promised_less_than_a_richer_one_and_neither_more_than_the_flat_figure(self):
        thin = StandInLabour(THIN_PURSE).room_added_by(FLAT_PLACES)
        rich = StandInLabour(RICH_PURSE).room_added_by(FLAT_PLACES)
        self.assertLess(thin, rich)
        self.assertLess(thin, FLAT_PLACES)
        self.assertLessEqual(rich, FLAT_PLACES)

    def test_the_advice_does_not_print_the_flat_figure_for_a_node_at_a_thin_income(self):
        advice = StandInLabour(THIN_PURSE)._room_advice()
        self.assertEqual([remedy["node"] for remedy in facts_of(advice)["remedies"] if remedy["action"] == "build"],
                         ["freedman_staff"])
        # presentation: the advice prints the figure the player reads, and says why it is not fixed
        text = str(advice)
        self.assertNotIn("freedman_staff (+%d places)" % FLAT_PLACES, text)
        self.assertIn("grow with surplus", text)


if __name__ == "__main__":
    unittest.main()

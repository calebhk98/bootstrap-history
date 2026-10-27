"""Complaint 163: the household-room advice (`labour`, the `hire` refusal) names `buy housing N` first, at the price
`quote housing` charges, and only then the tech nodes. The advice is sim/labour/room_advice.py, called on built facts."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.workforce.rules import price_of_labour_hours
from sim.labour.room_advice import hire_room_refusal, room_advice, sources_to_build, sources_to_reopen
from sim.refusal import cause_of, facts_of

PRICE_TEXT = "1,234 den"


def places_text(places):
    return "%g" % places


def advice(reopen=(), want=(), startable=True):
    return room_advice(PRICE_TEXT, list(reopen), list(want), startable, places_text)


def remedy_actions(refusal):
    return [remedy["action"] for remedy in facts_of(refusal)["remedies"]]


class AdviceOrderTests(unittest.TestCase):
    def test_buying_housing_comes_before_any_tech_node(self):
        refusal = advice(want=[("workshop_first", 6), ("school_founded", 4)])
        self.assertEqual(remedy_actions(refusal), ["buy_housing", "build", "build"])
        self.assertEqual([remedy["node"] for remedy in facts_of(refusal)["remedies"]],
                         [None, "workshop_first", "school_founded"])

    def test_reopening_what_is_shut_comes_before_building(self):
        refusal = advice(reopen=[("old_school", 5)], want=[("workshop_first", 6)])
        self.assertEqual(remedy_actions(refusal), ["buy_housing", "reopen", "build"])

    def test_housing_is_still_named_when_nothing_is_left_to_build(self):
        self.assertEqual(remedy_actions(advice()), ["buy_housing"])
        self.assertEqual(remedy_actions(advice(reopen=[("old_school", 5)])), ["buy_housing", "reopen"])

    def test_at_most_two_reopenings_and_three_buildings_are_named(self):
        refusal = advice(reopen=[("a", 3), ("b", 2), ("c", 1)], want=[("w%d" % number, 1) for number in range(6)])
        self.assertEqual(remedy_actions(refusal), ["buy_housing"] + ["reopen"] * 2 + ["build"] * 3)

    def test_the_cause_is_room_advice(self):
        self.assertEqual(cause_of(advice(want=[("workshop_first", 6)])), "room_advice")

    def test_the_price_given_is_the_price_the_advice_prints_for_one_place(self):
        # presentation: the advice quotes the per-place price it was given
        self.assertIn("adds N places at %s each" % PRICE_TEXT, str(advice(want=[("workshop_first", 6)])))
        self.assertIn(PRICE_TEXT, str(advice()))

    def test_the_advice_no_longer_claims_room_is_not_bought(self):
        # presentation: a sentence the advice must not say
        self.assertNotIn("Room is not bought", str(advice(want=[("workshop_first", 6)])))


class HousingPriceTests(unittest.TestCase):
    """`buy housing`, `quote housing` and the advice all read this one function."""

    def test_a_place_costs_its_hours_in_the_coin_times_the_price_level(self):
        self.assertAlmostEqual(price_of_labour_hours(40.0, 1.0, 1.5), 60.0)
        self.assertAlmostEqual(price_of_labour_hours(40.0, 0.5, 1.5), 30.0)


class SelectionTests(unittest.TestCase):
    SOURCES = [("near", 4), ("far", 130), ("shut_small", 2), ("shut_big", 9), ("unknown", 7), ("hidden", 7)]
    KNOWN = {"near", "far", "shut_small", "shut_big", "hidden"}

    def test_shut_sources_are_those_built_not_running_and_a_venture_biggest_first(self):
        shut = sources_to_reopen(self.SOURCES, done={"shut_small", "shut_big", "near"}, operating={"near"},
                                 known=self.KNOWN, is_venture=lambda node_id: True)
        self.assertEqual(shut, [("shut_big", 9), ("shut_small", 2)])

    def test_a_built_source_that_is_not_a_venture_cannot_be_reopened(self):
        shut = sources_to_reopen(self.SOURCES, done={"shut_big"}, operating=set(), known=self.KNOWN,
                                 is_venture=lambda node_id: False)
        self.assertEqual(shut, [])

    def test_sources_to_build_are_the_unbuilt_visible_known_ones_nearest_first(self):
        distances = {"near": 1, "far": 9, "hidden": 1}
        want = sources_to_build(self.SOURCES, done={"shut_big", "shut_small"}, known=self.KNOWN,
                                visible=lambda node_id: node_id != "hidden", distance=distances.__getitem__)
        self.assertEqual(want, [("near", 4), ("far", 130)])

    def test_equal_distance_puts_the_bigger_source_first(self):
        want = sources_to_build([("small", 2), ("big", 8)], done=set(), known={"small", "big"},
                                visible=lambda node_id: True, distance=lambda node_id: 3)
        self.assertEqual(want, [("big", 8), ("small", 2)])


class HireRefusalTests(unittest.TestCase):
    def refusal(self, room=2.97, count=7):
        return hire_room_refusal(room, count, advice(want=[("workshop_first", 6)]))

    def test_the_hire_refusal_has_its_cause_and_room(self):
        refusal = self.refusal()
        self.assertEqual(cause_of(refusal), "household_room")
        self.assertEqual(facts_of(refusal)["room"], 2.97)

    def test_it_carries_the_advice_remedies_with_housing_first(self):
        self.assertEqual(remedy_actions(self.refusal()), ["buy_housing", "build"])

    def test_the_room_is_truncated_never_rounded_up(self):
        # presentation: the room shown to the player
        text = str(self.refusal(room=6.999))
        self.assertIn("6.99 more people", text)
        self.assertIn("6 is the most whole people", text)

    def test_no_room_at_all_is_said_so(self):
        # presentation: wording for a household with no room
        self.assertIn("no room for even one", str(self.refusal(room=-3.0, count=1)))
        self.assertEqual(facts_of(self.refusal(room=-3.0, count=1))["room"], 0.0)

    def test_the_hire_refusal_names_buy_housing_before_the_nodes(self):
        # presentation: the order the text names things in
        text = str(self.refusal())
        self.assertLess(text.index("buy housing"), text.index("workshop_first"))


if __name__ == "__main__":
    unittest.main()

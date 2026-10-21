"""Complaint 190 and 640: the colony rules (`founding_refusal`, `advance_colony`) on plain inputs, no game."""

QUICK_TOPIC = True

import unittest

from sim.engine.colony_rules import WORKING_AGE_PER_SETTLER, advance_colony, founding_refusal
from sim.world import demography


def refusal(**overrides):
    inputs = dict(tile_held=False, reachable_by_land=True, reachable_by_sea=True, has_settlement_work=True,
                  working_age=1000.0, settlers=10.0, outfit_cost=50.0, spendable=100.0)
    inputs.update(overrides)
    return founding_refusal(**inputs)


class FoundingRefusal(unittest.TestCase):
    def test_a_reachable_affordable_free_tile_is_not_refused(self):
        self.assertIsNone(refusal())

    def test_a_held_tile_is_refused_first(self):
        self.assertEqual(refusal(tile_held=True, reachable_by_land=False, reachable_by_sea=False), "tile_held")

    def test_a_tile_reachable_neither_way_is_unreachable(self):
        self.assertEqual(refusal(reachable_by_land=False, reachable_by_sea=False), "unreachable")

    def test_reachable_by_sea_alone_is_enough(self):
        self.assertIsNone(refusal(reachable_by_land=False))

    def test_no_known_work_for_the_route_is_refused(self):
        self.assertEqual(refusal(has_settlement_work=False), "no_settlement_work")

    def test_too_few_working_age_people_is_refused_at_the_reserve(self):
        self.assertEqual(refusal(working_age=WORKING_AGE_PER_SETTLER * 10.0 - 1.0), "too_few_people")
        self.assertIsNone(refusal(working_age=WORKING_AGE_PER_SETTLER * 10.0))

    def test_an_outfit_past_what_can_be_raised_is_refused(self):
        self.assertEqual(refusal(outfit_cost=100.01, spendable=100.0), "cannot_afford")
        self.assertIsNone(refusal(outfit_cost=100.0, spendable=100.0))


class FakePeople:
    """Each year the working-age number is halved and the other cohorts keep what they had."""

    def __init__(self, children, working_age, elderly):
        self.children, self.working_age, self.elderly = children, working_age, elderly

    def step(self, food, jitter, disease_burden):
        self.seen = (food, jitter, disease_burden)
        self.working_age /= 2.0

    @property
    def total(self):
        return self.children + self.working_age + self.elderly


class AdvanceColony(unittest.TestCase):
    def test_the_hands_set_the_food_and_the_people_are_written_back(self):
        colony = {"tile": "t", "children": 1.0, "working_age": 40.0, "elderly": 2.0}
        seen = []
        died = advance_colony(colony, lambda hands: seen.append(hands) or hands * 3.0, FakePeople, 0.25)
        self.assertEqual(seen, [40.0])
        self.assertEqual((colony["children"], colony["working_age"], colony["elderly"]), (1.0, 20.0, 2.0))
        self.assertFalse(died)

    def test_fewer_than_one_person_left_is_died_out(self):
        colony = {"children": 0.2, "working_age": 0.2, "elderly": 0.2}
        self.assertTrue(advance_colony(colony, lambda hands: 0.0, FakePeople, 0.0))

    def test_exactly_one_person_left_is_not_died_out(self):
        colony = {"children": 0.5, "working_age": 1.0, "elderly": 0.0}
        self.assertFalse(advance_colony(colony, lambda hands: 0.0, FakePeople, 0.0))

    def test_real_people_with_plenty_of_food_grow_and_age_into_all_cohorts(self):
        colony = {"children": 0.0, "working_age": 200.0, "elderly": 0.0}
        for _year in range(40):
            self.assertFalse(advance_colony(colony, lambda hands: 1.0e12, demography.Population, 0.0))
        self.assertGreater(colony["children"] + colony["working_age"] + colony["elderly"], 400.0)
        self.assertGreater(colony["children"], 0.0)
        self.assertGreater(colony["elderly"], 0.0)

    def test_real_people_with_no_food_shrink_year_on_year(self):
        colony = {"children": 5.0, "working_age": 20.0, "elderly": 2.0}
        totals = []
        for _year in range(10):
            advance_colony(colony, lambda hands: 0.0, demography.Population, 0.0)
            totals.append(colony["children"] + colony["working_age"] + colony["elderly"])
        self.assertTrue(all(later < earlier for earlier, later in zip(totals, totals[1:])), totals)


if __name__ == "__main__":
    unittest.main()

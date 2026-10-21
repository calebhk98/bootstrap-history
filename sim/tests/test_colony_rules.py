"""Complaint 190 and 640: the colony rules (`founding_refusal`, `advance_colony`) on plain inputs, no game."""

QUICK_TOPIC = True

import unittest

from sim.engine.colony_rules import (WORKING_AGE_PER_SETTLER, advance_colony, best_settlement_work, colony_people,
                                     founding_refusal, outfit_cost)
from sim.geography.api import settlement
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


class Settlement(unittest.TestCase):
    """The work chosen, the outfit and the head count (colony_rules), and the tiles settlers can reach (the geography)."""

    WORKS = [("small_charter", {"settlers": 50, "outfit_hours_per_settler": 100.0}),
             ("big_sea_charter", {"settlers": 200, "outfit_hours_per_settler": 100.0, "by_sea": True}),
             ("big_land_charter", {"settlers": 200, "outfit_hours_per_settler": 100.0})]

    def test_the_work_that_sends_the_most_settlers_is_chosen_and_ties_go_by_id(self):
        self.assertEqual(best_settlement_work(self.WORKS, False)[0], "big_sea_charter")
        self.assertIsNone(best_settlement_work([], False))

    def test_a_voyage_by_sea_needs_a_work_that_crosses_the_sea(self):
        self.assertEqual(best_settlement_work(self.WORKS, True)[0], "big_sea_charter")
        self.assertIsNone(best_settlement_work(self.WORKS[:1], True))
        self.assertEqual(best_settlement_work(self.WORKS[:1], False)[0], "small_charter")

    def test_the_outfit_is_each_settlers_hours_at_the_money_per_hour(self):
        self.assertAlmostEqual(outfit_cost({"settlers": 20, "outfit_hours_per_settler": 50.0}, 2.5), 2500.0)

    def test_a_colonys_people_are_its_three_cohorts(self):
        self.assertEqual(colony_people({"children": 1.0, "working_age": 20.0, "elderly": 3.0}), 24.0)

    def test_settlers_reach_tiles_that_border_what_is_held_and_not_the_held_tiles_themselves(self):
        from sim.engine.data import load_civ
        from sim.geography.api import tiles_held
        held = tiles_held(load_civ("rome_100ad"))
        reachable = settlement.candidate_tiles(held, [])
        self.assertTrue(reachable)
        self.assertFalse(set(reachable) & set(held))

    def test_the_tiles_are_listed_best_land_first_and_a_claimed_tile_is_not_offered(self):
        from sim.engine.data import load_civ
        from sim.geography.api import tiles_held
        held = tiles_held(load_civ("rome_100ad"))
        reachable = settlement.candidate_tiles(held, [])
        capacities = [settlement.capacity_kcal_per_day(tile) for tile in reachable]
        self.assertEqual(capacities, sorted(capacities, reverse=True))
        self.assertNotIn(reachable[0], settlement.candidate_tiles(held, [reachable[0]]))

    def test_by_sea_any_coast_is_reachable_from_a_coast_which_is_many_more_tiles(self):
        from sim.engine.data import load_civ
        from sim.geography.api import tiles_held
        held = tiles_held(load_civ("rome_100ad"))
        self.assertGreater(len(settlement.candidate_tiles(held, [], True)), len(settlement.candidate_tiles(held, [])))

    def test_no_hands_raise_no_food_and_many_hands_raise_the_whole_of_what_the_land_gives(self):
        from sim.engine.data import load_civ
        from sim.geography.api import tiles_held
        tile = settlement.candidate_tiles(tiles_held(load_civ("rome_100ad")), [])[0]
        capacity = settlement.capacity_kcal_per_day(tile)
        self.assertEqual(settlement.worked_kcal_per_day(tile, 0.0), 0.0)
        self.assertLess(settlement.worked_kcal_per_day(tile, 1.0), settlement.worked_kcal_per_day(tile, 1000.0))
        self.assertLess(settlement.worked_kcal_per_day(tile, 1000.0), capacity)
        self.assertAlmostEqual(settlement.worked_kcal_per_day(tile, 1.0e12), capacity, delta=1e-6 * capacity)


if __name__ == "__main__":
    unittest.main()

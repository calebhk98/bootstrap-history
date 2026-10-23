"""The people of a trade who exist bound what a market offers and what can be hired (`labour/trade_supply_rules.py`, used by
`Labour.market_supply`, `people_who_exist` and `hire`), over a spread of nation sizes."""
QUICK_TOPIC = True

import unittest

from sim.labour.trade_supply_rules import hire_leaves_nobody, people_who_exist, supply_hours

HOURS_PER_PERSON_YEAR = 2000.0
NATION_SIZES = (50000.0, 5000.0, 200.0, 30.0)


class PeopleWhoExistTest(unittest.TestCase):
    def test_the_estimate_stands_when_it_exceeds_the_household_staff(self):
        self.assertEqual(people_who_exist(40.0, 3.0), 40.0)

    def test_the_household_staff_count_even_when_a_collapse_leaves_the_estimate_below_them(self):
        self.assertEqual(people_who_exist(1.5, 4.0), 4.0)


class SupplyHoursTest(unittest.TestCase):
    def test_the_market_never_offers_more_hours_than_the_existing_people_work(self):
        for nation in NATION_SIZES:
            existing = people_who_exist(nation * 0.01, 0.0)
            offered = supply_hours(1e12, existing, HOURS_PER_PERSON_YEAR)
            self.assertEqual(offered / HOURS_PER_PERSON_YEAR, existing, nation)
            self.assertLessEqual(offered / HOURS_PER_PERSON_YEAR, nation, nation)

    def test_a_smaller_offer_is_not_raised_to_the_people_who_exist(self):
        self.assertEqual(supply_hours(3000.0, 10.0, HOURS_PER_PERSON_YEAR), 3000.0)


class HireLeavesNobodyTest(unittest.TestCase):
    def test_hiring_more_than_exist_is_refused(self):
        self.assertTrue(hire_leaves_nobody(on_books=0.0, rivals_staff=0.0, count=5.0, people_existing=2.0))

    def test_firms_and_the_state_staff_count_against_the_people_who_exist(self):
        self.assertTrue(hire_leaves_nobody(on_books=1.0, rivals_staff=3.0, count=1.0, people_existing=4.5))
        self.assertFalse(hire_leaves_nobody(on_books=1.0, rivals_staff=2.0, count=1.0, people_existing=4.0))

    def test_hiring_exactly_the_last_person_is_allowed(self):
        self.assertFalse(hire_leaves_nobody(on_books=2.0, rivals_staff=0.0, count=1.0, people_existing=3.0))


if __name__ == "__main__":
    unittest.main()

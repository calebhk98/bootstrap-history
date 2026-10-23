"""`CollectionView`: the state's employed officials, guards, inspectors and foresters are what each line asks for less the share of
its pay left unpaid, and each staff's share of the people moves only with its own line (Complaints 620, 660). Called on a small
subclass whose world readers are written out."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest

from sim.agents import budget
from sim.agents.collection_world import CollectionView

PEOPLE = 40_000.0
PAY = 10.0


class OneTileWorld(CollectionView):
    hours_per_person_year = 2000.0

    def __init__(self, unfunded=None):
        self.record = SimpleNamespace(unfunded=dict(unfunded or {}), hold_by_tile={})

    def government(self):
        return SimpleNamespace(record=self.record)

    def pay_per_person_year(self, trade):
        return PAY

    def population_total(self):
        return PEOPLE

    def literacy(self, name):
        return 0.0

    def collection_people_by_tile(self):
        return {"seat": PEOPLE}

    def collection_modes(self):
        return ()


class StaffEmployed(unittest.TestCase):
    def test_a_line_with_nothing_unpaid_employs_all_it_keeps(self):
        self.assertEqual(OneTileWorld().staff_employed("administration", "scribe", 100.0), 100.0)

    def test_the_unpaid_share_of_pay_is_the_share_of_staff_not_employed(self):
        self.assertEqual(OneTileWorld({"administration": 250.0}).staff_employed("administration", "scribe", 100.0), 75.0)

    def test_the_officials_kept_follow_the_people_over_the_administrative_span(self):
        self.assertAlmostEqual(OneTileWorld().officials_employed(), PEOPLE / budget.ADMINISTRATIVE_SPAN)

    def test_officials_nearly_all_unpaid_employ_almost_none(self):
        kept = PEOPLE / budget.ADMINISTRATIVE_SPAN
        starved = OneTileWorld({"administration": 0.999 * kept * PAY})
        self.assertLess(starved.officials_employed(), 0.01 * kept + 1e-9)


class SharesFollowTheirOwnStaff(unittest.TestCase):
    def test_unpaid_officials_collect_less(self):
        kept = PEOPLE / budget.ADMINISTRATIVE_SPAN
        fed = OneTileWorld().collectible_share()
        starved = OneTileWorld({"administration": 0.999 * kept * PAY}).collectible_share()
        self.assertLess(starved, fed)
        self.assertTrue(0.0 <= starved <= fed <= 1.0)

    def test_unpaid_guards_leave_the_collection_and_inspection_shares_alone(self):
        fed, no_guards = OneTileWorld(), OneTileWorld({"guards": 1.0e12})
        self.assertEqual(no_guards.collectible_share(), fed.collectible_share())
        self.assertEqual(no_guards.inspection_share(), fed.inspection_share())
        self.assertLess(no_guards.order_share(), fed.order_share())

    def test_unpaid_inspectors_lower_only_the_inspection_share(self):
        fed, no_inspectors = OneTileWorld(), OneTileWorld({"inspectors": 1.0e12})
        self.assertLess(no_inspectors.inspection_share(), fed.inspection_share())
        self.assertEqual(no_inspectors.order_share(), fed.order_share())
        self.assertEqual(no_inspectors.forest_share(), fed.forest_share())

    def test_unpaid_foresters_lower_only_the_forest_share(self):
        fed, no_foresters = OneTileWorld(), OneTileWorld({"foresters": 1.0e12})
        self.assertLess(no_foresters.forest_share(), fed.forest_share())
        self.assertEqual(no_foresters.order_share(), fed.order_share())
        self.assertEqual(no_foresters.inspection_share(), fed.inspection_share())


if __name__ == "__main__":
    unittest.main()

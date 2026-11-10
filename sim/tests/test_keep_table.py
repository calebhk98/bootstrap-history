"""plan_keeps: the owner's purse is drawn down in row order, and the first payment it cannot cover ends the following of that owner."""
QUICK_TOPIC = True

import unittest

from sim.agents.keep_table import KEEPS, OWNERS, KeepOwners, Keeps, keep_due, plan_keeps


def table(owner, members, cost, allowance, product, top_up, purses, known=None):
    keeps = KEEPS.table_of(Keeps, owner=owner, members=members, cost_per_person=cost, allowance=allowance,
                           labour_product=product, top_up=top_up, due=[0.0] * len(owner), covered=[0] * len(owner))
    owners = OWNERS.table_of(KeepOwners, purse=purses, known=known or [1] * len(purses))
    return keeps, owners


class KeepDueTests(unittest.TestCase):
    def test_a_top_up_pays_only_the_part_beyond_the_allowance(self):
        self.assertEqual(keep_due(10.0, 3.0, 12.0, 1), 18.0)

    def test_a_top_up_pays_nothing_when_the_allowance_covers_the_cost(self):
        self.assertEqual(keep_due(10.0, 3.0, 40.0, 1), 0.0)

    def test_a_settlement_pays_the_whole_cost(self):
        self.assertEqual(keep_due(10.0, 3.0, 40.0, 0), 30.0)


class PlanKeepsTests(unittest.TestCase):
    def test_the_purse_is_drawn_down_in_row_order(self):
        keeps, owners = table([0, 0, 0], [1.0] * 3, [40.0, 70.0, 5.0], [0.0] * 3, [0.0] * 3, [1] * 3, [100.0])
        plan_keeps(keeps, owners)
        # 40 is paid; 70 is more than the 60 left, and then the owner is not followed, so 5 is left to the Python rule too
        self.assertEqual(keeps.covered.tolist(), [1, 0, 0])
        self.assertEqual(owners.known.tolist(), [0])
        self.assertEqual(owners.purse.tolist(), [60.0])

    def test_two_owners_are_followed_separately(self):
        keeps, owners = table([0, 1, 0], [1.0] * 3, [70.0, 70.0, 70.0], [0.0] * 3, [0.0] * 3, [1] * 3, [100.0, 100.0])
        plan_keeps(keeps, owners)
        self.assertEqual(keeps.covered.tolist(), [1, 1, 0])

    def test_the_labour_product_is_in_the_purse_before_the_payment(self):
        keeps, owners = table([0], [1.0], [150.0], [0.0], [100.0], [0], [60.0])
        plan_keeps(keeps, owners)
        self.assertEqual((keeps.covered.tolist(), owners.purse.tolist()), ([1], [10.0]))

    def test_an_owner_not_followed_has_nothing_covered(self):
        keeps, owners = table([0], [1.0], [10.0], [0.0], [0.0], [0], [100.0], known=[0])
        plan_keeps(keeps, owners)
        self.assertEqual(keeps.covered.tolist(), [0])

    def test_a_row_owing_nothing_is_not_covered_and_leaves_the_purse(self):
        keeps, owners = table([0], [1.0], [10.0], [20.0], [0.0], [1], [100.0])
        plan_keeps(keeps, owners)
        self.assertEqual((keeps.due.tolist(), keeps.covered.tolist(), owners.purse.tolist()), ([0.0], [0], [100.0]))

    def test_a_payment_at_the_dust_level_is_covered_and_costs_the_purse_nothing(self):
        keeps, owners = table([0], [1.0], [1e-10], [0.0], [0.0], [0], [0.0])
        plan_keeps(keeps, owners)
        self.assertEqual((keeps.covered.tolist(), owners.purse.tolist()), ([1], [0.0]))


if __name__ == "__main__":
    unittest.main()

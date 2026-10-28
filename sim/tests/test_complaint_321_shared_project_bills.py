"""Complaint 321: what a project costs in materials does not depend on the firm pricing it, so a yearly turn computes
each project's material bill once however many firms price it, and never serves a bill the market has since moved
under. The rule is the shared-answer table of sim/engine/view_share.py, called on a stand-in world whose stamp the test
moves. (That firms' copy pricing goes through it: test_sim_world_copy_cost_scope.)"""
QUICK_TOPIC = True

import unittest

from sim.engine.view_share import ViewShare

from sim.tests.ui_stand_in import FactViews

class World(ViewShare, FactViews):
    """A world that has a price table (compared by identity), a year and a stock count (compared by value)."""

    def __init__(self):
        super().__init__(self)     # the world is also the game the service reads the stock of
        self.prices = {"iron": 5.0}
        self.year = 100
        self.stock = {"iron": 0.0}
        self.computed = 0

    def _view_world_stamp(self):
        return ((self.prices,), (self.year,))

    def _standalone_stamp(self):
        return ((), (self.year,))

    def material_stock_t(self, key):
        return self.stock[key]

    def _shared_bill_keys(self, node_id):
        return ("iron",)

    def price(self, inputs=("a",), standalone=False, key="bill-a"):
        def compute():
            self.computed += 1
            return self.computed * 10.0
        return self._shared_answer(key, inputs, compute, standalone)


class SharedAnswerTests(unittest.TestCase):
    def test_outside_a_view_nothing_is_shared(self):
        world = World()
        world.price()
        world.price()
        self.assertEqual(world.computed, 2)

    def test_inside_a_view_an_answer_is_computed_once_however_many_ask(self):
        world = World()
        opened = world.open_view_scope({})
        answers = {world.price() for _ in range(40)}
        world.close_view_scope(opened)
        self.assertEqual(world.computed, 1)
        self.assertEqual(len(answers), 1)

    def test_forty_askers_compute_no_more_than_three(self):
        def computations(askers):
            world = World()
            opened = world.open_view_scope({})
            for _ in range(askers):
                world.price()
                world.price(key="bill-b")
            world.close_view_scope(opened)
            return world.computed
        self.assertEqual(computations(40), computations(3))

    def test_different_inputs_are_different_answers(self):
        world = World()
        opened = world.open_view_scope({})
        first, second = world.price(inputs=("a",)), world.price(inputs=("b",))
        world.close_view_scope(opened)
        self.assertNotEqual(first, second)
        self.assertEqual(world.computed, 2)

    def test_a_bill_is_not_served_after_the_price_table_was_rebuilt(self):
        world = World()
        opened = world.open_view_scope({})
        first = world.price()
        world.prices = {"iron": 9.0}        # a new table: the market moved
        second = world.price()
        world.close_view_scope(opened)
        self.assertNotEqual(first, second)

    def test_a_bill_is_not_served_after_a_stamped_value_moved(self):
        world = World()
        opened = world.open_view_scope({})
        world.price()
        world.year += 1
        world.price()
        world.close_view_scope(opened)
        self.assertEqual(world.computed, 2)

    def test_a_world_with_no_stamp_shares_nothing(self):
        world = World()
        world._view_world_stamp = lambda: None
        opened = world.open_view_scope({})
        world.price()
        world.price()
        world.close_view_scope(opened)
        self.assertEqual(world.computed, 2)

    def test_a_standalone_answer_is_shared_outside_a_view(self):
        world = World()
        world.price(standalone=True)
        world.price(standalone=True)
        self.assertEqual(world.computed, 1)

    def test_closing_a_view_leaves_no_scope_open_on_the_founders_own_pricing(self):
        world = World()
        opened = world.open_view_scope({})
        world.price()
        world.close_view_scope(opened)
        self.assertIsNone(world._view_scope)
        world.price()
        self.assertEqual(world.computed, 2)

    def test_nested_views_hand_back_the_outer_scope(self):
        world = World()
        outer = {}
        first = world.open_view_scope(outer)
        second = world.open_view_scope({})
        world.close_view_scope(second)
        self.assertIs(world._view_scope, outer)
        world.close_view_scope(first)
        self.assertIsNone(world._view_scope)


class SharedBillTests(unittest.TestCase):
    def test_a_bill_is_reused_while_the_nodes_stock_holds(self):
        world = World()
        bills = []
        opened = world.open_view_scope({})
        for _ in range(5):
            bills.append(world._shared_bill("project", lambda: world.price(key="inner")))
        world.close_view_scope(opened)
        self.assertEqual(len(set(bills)), 1)

    def test_a_bill_is_recomputed_when_the_stock_it_draws_on_moved(self):
        world = World()
        computed = []
        opened = world.open_view_scope({})
        world._shared_bill("project", lambda: computed.append(1))
        world.stock["iron"] = 1.0e6
        world._shared_bill("project", lambda: computed.append(1))
        world.close_view_scope(opened)
        self.assertEqual(len(computed), 2)

    def test_outside_a_view_every_bill_is_computed(self):
        world = World()
        computed = []
        world._shared_bill("project", lambda: computed.append(1))
        world._shared_bill("project", lambda: computed.append(1))
        self.assertEqual(len(computed), 2)


if __name__ == "__main__":
    unittest.main()

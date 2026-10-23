"""`Government.employ_standing`, `seek_shortfall` and `spend_on_lines`: where the state's standing lines reach the labour pool, the
levy rates and the goods market. Each is called on a stand-in `self` and world carrying only what it reads."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest
from unittest import mock

from sim.agents import government
from sim.agents.budget import LEVY_RATE_CEILING
from sim.agents.budget_line import Line
from sim.agents.edges import EDGE_STATE_SPENDING
from sim.agents.government import Government


class EmployStanding(unittest.TestCase):
    def test_each_trades_people_reach_the_workforce_as_far_as_the_world_says_and_add_to_it(self):
        world = SimpleNamespace(local_staff=lambda trade, people: people * 0.1)
        stand_in = SimpleNamespace(workforce={"scribe": 1.0})
        lines = [Line("army", "requisition", labour={"soldier": 100.0}), Line("administration", "office", labour={"scribe": 10.0})]
        Government.employ_standing(stand_in, lines, 0.5, world)
        self.assertEqual(stand_in.workforce, {"soldier": 5.0, "scribe": 1.5})


class SeekShortfall(unittest.TestCase):
    def stand_in(self, sought):
        record = SimpleNamespace(levy_base=None, levy_requisition_rate=None, levy_office_rate=None)
        return SimpleNamespace(record=record, levy_sought=lambda: sought)

    def world(self, payers):
        return SimpleNamespace(visible_taxpayers=lambda: payers, notice_over=lambda scale: scale)

    def test_the_base_is_the_visible_income_weighted_by_notice_and_the_rate_is_shortfall_over_it(self):
        stand_in = self.stand_in({"army": 100.0, "administration": 100.0})
        lines = [Line("army", "requisition"), Line("administration", "office")]
        Government.seek_shortfall(stand_in, lines, self.world([(1.0, 2000.0), (0.5, 4000.0)]))
        self.assertEqual(stand_in.record.levy_base, 4000.0)
        self.assertAlmostEqual(stand_in.record.levy_requisition_rate, 0.025)
        self.assertAlmostEqual(stand_in.record.levy_office_rate, 0.025)

    def test_nothing_sought_sets_no_rates(self):
        stand_in = self.stand_in({})
        Government.seek_shortfall(stand_in, [Line("army", "requisition")], self.world([(1.0, 1000.0)]))
        self.assertEqual((stand_in.record.levy_requisition_rate, stand_in.record.levy_office_rate), (0.0, 0.0))

    def test_nothing_visible_asks_the_ceiling(self):
        stand_in = self.stand_in({"army": 100.0})
        Government.seek_shortfall(stand_in, [Line("army", "requisition")], self.world([]))
        self.assertEqual(stand_in.record.levy_requisition_rate, LEVY_RATE_CEILING)


class SpendOnLines(unittest.TestCase):
    def run_lines(self, lines, share):
        wages, bids, transfers = [], [], []
        world = SimpleNamespace(pay_wages=lambda actor, money, name: wages.append((name, money)),
                                market_purchase=lambda buyer, commodity, tonnes, money: bids.append((buyer, commodity, tonnes, money)),
                                edge=lambda name: name)
        stand_in = SimpleNamespace(actor_id="state")
        with mock.patch.object(government.ledger, "transfer", lambda payer, edge, money, purpose: transfers.append((edge, money, purpose))):
            Government.spend_on_lines(stand_in, lines, share, world)
        return wages, bids, transfers

    def test_a_staffed_line_pays_its_wages_into_the_labour_market_less_what_it_bids_for_goods(self):
        line = Line("army", "requisition", labour={"soldier": 10.0}, wages=80.0, materials={"iron": 4.0}, material_cost=20.0)
        wages, bids, transfers = self.run_lines([line], 0.5)
        self.assertEqual(wages, [("army", 40.0)])
        self.assertEqual(transfers, [])

    def test_materials_are_bid_for_at_the_funded_share_split_by_tonnes(self):
        line = Line("army", "requisition", labour={"soldier": 10.0}, wages=80.0, materials={"iron": 3.0, "wood": 1.0}, material_cost=20.0)
        _wages, bids, _transfers = self.run_lines([line], 0.5)
        self.assertEqual(bids, [("state", "iron", 1.5, 7.5), ("state", "wood", 0.5, 2.5)])

    def test_a_line_with_no_staff_goes_out_to_the_spending_edge(self):
        line = Line("roads", "office", transfer=60.0)
        wages, _bids, transfers = self.run_lines([line], 0.5)
        self.assertEqual((wages, transfers), ([], [(EDGE_STATE_SPENDING, 30.0, "roads")]))

    def test_nothing_funded_pays_no_money_but_still_asks_for_goods_at_no_tonnes(self):
        line = Line("army", "requisition", labour={"soldier": 10.0}, wages=80.0, materials={"iron": 4.0}, material_cost=20.0)
        wages, bids, transfers = self.run_lines([line], 0.0)
        self.assertEqual((wages, transfers, bids), ([], [], [("state", "iron", 0.0, 0.0)]))


if __name__ == "__main__":
    unittest.main()

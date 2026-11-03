"""`Government.employ_standing`, `seek_shortfall` and `spend_on_lines`: where the state's standing lines reach the labour pool, the
levy rates and the goods market. Each is called on a stand-in `self` and world carrying only what it reads."""

QUICK_TOPIC = True

from sim.tests.agents_fake_world import flat_namespace
from types import SimpleNamespace
import unittest
from unittest import mock

from sim.book import InsufficientFunds

from sim.agents import government
from sim.agents.budget import LEVY_RATE_CEILING
from sim.agents.budget_line import Line
from sim.agents.edges import EDGE_STATE_SPENDING
from sim.agents.government import Government


class EmployStanding(unittest.TestCase):
    def test_each_trades_people_are_posted_at_the_funded_share_and_add_to_the_places_already_posted(self):
        world = SimpleNamespace()
        stand_in = SimpleNamespace(staff_wanted={"scribe": 1.0})
        lines = [Line("army", "requisition", labour={"soldier": 100.0}), Line("administration", "office", labour={"scribe": 10.0})]
        Government.employ_standing(stand_in, lines, 0.5, world)
        self.assertEqual(stand_in.staff_wanted, {"soldier": 50.0, "scribe": 6.0})


class SeekShortfall(unittest.TestCase):
    def stand_in(self, sought):
        record = SimpleNamespace(levy_base=None, levy_requisition_rate=None, levy_office_rate=None)
        return SimpleNamespace(record=record, fiscal=SimpleNamespace(levy_sought=lambda: sought))

    def world(self, payers):
        return flat_namespace(visible_taxpayers=lambda: payers, notice_over=lambda scale: scale)

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


class SpendWhatItCan(unittest.TestCase):
    def spend(self, money, refuse_above):
        paid = []

        def transfer(payer, edge, amount, purpose):
            if amount > refuse_above:
                raise InsufficientFunds("lenders hold no such sum")
            paid.append(amount)
        with mock.patch.object(government.ledger, "transfer", transfer):
            government._spend_what_it_can(SimpleNamespace(money=money), "edge", 100.0, "roads")
        return paid

    def test_a_payment_the_lenders_refuse_is_cut_to_the_purse(self):
        self.assertEqual(self.spend(40.0, 50.0), [40.0])

    def test_a_state_with_nothing_in_its_purse_spends_nothing(self):
        self.assertEqual(self.spend(-30.0, 50.0), [])

    def test_a_payment_the_lenders_allow_is_made_in_full(self):
        self.assertEqual(self.spend(0.0, 1000.0), [100.0])


class SpendOnLines(unittest.TestCase):
    def run_lines(self, lines, share):
        bids, transfers = [], []
        world = flat_namespace(market_purchase=lambda buyer, commodity, tonnes, money: bids.append((buyer, commodity, tonnes, money)),
                                edge=lambda name: name)
        stand_in = SimpleNamespace(actor_id="state")
        with mock.patch.object(government.ledger, "transfer", lambda payer, edge, money, purpose: transfers.append((edge, money, purpose))):
            Government.spend_on_lines(stand_in, lines, share, world)
        return bids, transfers

    def test_a_staffed_line_pays_nothing_out_of_the_purse_here_its_pay_is_offered_in_the_labour_market(self):
        line = Line("army", "requisition", labour={"soldier": 10.0}, wages=80.0, materials={"iron": 4.0}, material_cost=20.0)
        _bids, transfers = self.run_lines([line], 0.5)
        self.assertEqual(transfers, [])

    def test_materials_are_bid_for_at_the_funded_share_split_by_tonnes(self):
        line = Line("army", "requisition", labour={"soldier": 10.0}, wages=80.0, materials={"iron": 3.0, "wood": 1.0}, material_cost=20.0)
        bids, _transfers = self.run_lines([line], 0.5)
        self.assertEqual(bids, [("state", "iron", 1.5, 7.5), ("state", "wood", 0.5, 2.5)])

    def test_a_line_with_no_staff_goes_out_to_the_spending_edge(self):
        line = Line("roads", "office", transfer=60.0)
        _bids, transfers = self.run_lines([line], 0.5)
        self.assertEqual(transfers, [(EDGE_STATE_SPENDING, 30.0, "roads")])

    def test_nothing_funded_pays_no_money_but_still_asks_for_goods_at_no_tonnes(self):
        line = Line("army", "requisition", labour={"soldier": 10.0}, wages=80.0, materials={"iron": 4.0}, material_cost=20.0)
        bids, transfers = self.run_lines([line], 0.0)
        self.assertEqual((transfers, bids), ([], [("state", "iron", 0.0, 0.0)]))


if __name__ == "__main__":
    unittest.main()

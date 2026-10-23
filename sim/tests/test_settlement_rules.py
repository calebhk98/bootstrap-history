"""settle_insolvency on a stand-in debtor: what a settlement does to the purse, the name, credit and what is built."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.refusal import facts_of

from sim.engine import economy_credit
from sim.engine.economy_credit import CreditMixin


class Debtor(CreditMixin):
    """The parts of a Sim that settling touches; `lines` records what the ledger is told."""

    def __init__(self):
        self.lines = []
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(capital=-3000.0, reputation=50.0, log=[], credit_frozen_until=0),
            projects=types.SimpleNamespace(done={"identity_cover", "civ_road_paved"}, granted=set()))
        self.household = self.state.household

    def credit_limit(self, _rev=None, _upkeep=None, _capital=None):
        return 1000.0

    def edge(self, edge_id):
        return edge_id


def settle(debtor, year=100, limit=1000.0):
    ledger_stub = types.SimpleNamespace(settle=lambda book, edge, amount, text: debtor.lines.append(amount))
    with mock.patch.object(economy_credit, "ledger", ledger_stub):
        debtor.settle_insolvency(year, limit)


class SettleInsolvency(unittest.TestCase):

    def test_what_is_owed_after_the_write_off_is_the_retained_share_of_the_line(self):
        debtor = Debtor()
        settle(debtor)
        self.assertAlmostEqual(abs(debtor.lines[0]), 1000.0 * debtor.SETTLEMENT_CAPITAL_RETAINED_FRACTION)

    def test_a_settlement_never_abandons_a_persona_or_institution(self):
        debtor = Debtor()
        before = set(debtor.state.projects.done)
        settle(debtor)
        self.assertEqual(debtor.state.projects.done, before)

    def test_the_settlement_freezes_credit_for_the_declared_years(self):
        debtor = Debtor()
        settle(debtor, year=100)
        self.assertEqual(debtor.state.household.credit_frozen_until, 100 + debtor.SETTLEMENT_CREDIT_FREEZE_YEARS)

    def test_the_settlement_is_logged_with_the_hit_taken_as_a_field(self):
        debtor = Debtor()
        settle(debtor)
        (_year, line), = debtor.state.household.log
        self.assertEqual(line.kind, "insolvency_settled")
        self.assertAlmostEqual(line.facts["reputation_hit"], debtor.SETTLEMENT_REPUTATION_HIT)
        self.assertEqual(debtor.state.household.reputation, 50.0 - debtor.SETTLEMENT_REPUTATION_HIT)

    def test_settling_inside_an_earlier_freeze_pushes_the_date_out_and_records_both_dates(self):
        debtor = Debtor()
        debtor.state.household.credit_frozen_until = 110
        settle(debtor, year=105)
        (_year, line), = debtor.state.household.log
        self.assertEqual(debtor.state.household.credit_frozen_until, 105 + debtor.SETTLEMENT_CREDIT_FREEZE_YEARS)
        self.assertTrue(facts_of(line)["freeze_moved"])
        self.assertEqual(facts_of(line)["frozen_before"], 110)


if __name__ == "__main__":
    unittest.main()

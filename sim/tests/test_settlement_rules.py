"""settle_insolvency on the finance module: what a settlement does to the purse, the name, credit and what is built."""

QUICK_TOPIC = True

import unittest

from sim.agents.api import edges
from sim.finance.constants import SETTLEMENT_CAPITAL_RETAINED_FRACTION, SETTLEMENT_CREDIT_FREEZE_YEARS, SETTLEMENT_REPUTATION_HIT
from sim.ledger.api import SettleWithEdge
from sim.polity.api import SetReputation
from sim.reporting.api import RecordEvent
from sim.tests import finance_host, module_harness


class Debtor:
    """The finance module of a household 3000 in debt with a name of 50; `lines` records what the ledger is told."""

    def __init__(self):
        self.lines = []
        self.standing = 50.0
        self.projects_done = {"identity_cover", "civ_road_paved"}
        self.module = finance_host.build(
            answers={SetReputation: self.set_standing}, acting_balance=-3000.0, standing=lambda: {"reputation": self.standing},
            legacy_edge_account={edges.EDGE_CREDITORS: "creditors"})
        self.module.credit_limit = lambda revenue=None, upkeep=None, capital=None: 1000.0

    def set_standing(self, command):
        self.standing = command.value

    @property
    def log(self):
        return [command for command in module_harness.sent(self.module) if isinstance(command, RecordEvent)]


def settle(debtor, year=100, limit=1000.0):
    debtor.module.settle_insolvency(year, limit)
    debtor.lines = [command.balance for command in module_harness.sent(debtor.module) if isinstance(command, SettleWithEdge)]


class SettleInsolvency(unittest.TestCase):

    def test_what_is_owed_after_the_write_off_is_the_retained_share_of_the_line(self):
        debtor = Debtor()
        settle(debtor)
        self.assertAlmostEqual(abs(debtor.lines[0]), 1000.0 * SETTLEMENT_CAPITAL_RETAINED_FRACTION)

    def test_a_settlement_never_abandons_a_persona_or_institution(self):
        debtor = Debtor()
        before = set(debtor.projects_done)
        settle(debtor)
        self.assertEqual(debtor.projects_done, before)

    def test_the_settlement_freezes_credit_for_the_declared_years(self):
        debtor = Debtor()
        settle(debtor, year=100)
        self.assertEqual(debtor.module.seat.credit_frozen_until, 100 + SETTLEMENT_CREDIT_FREEZE_YEARS)
        self.assertEqual(debtor.module.seat.last_settlement, 100)

    def test_the_settlement_is_logged_with_the_hit_taken_as_a_field(self):
        debtor = Debtor()
        settle(debtor)
        event, = debtor.log
        self.assertEqual(event.kind, "insolvency_settled")
        self.assertAlmostEqual(event.facts["reputation_hit"], SETTLEMENT_REPUTATION_HIT)
        self.assertEqual(debtor.standing, 50.0 - SETTLEMENT_REPUTATION_HIT)

    def test_settling_inside_an_earlier_freeze_pushes_the_date_out_and_records_both_dates(self):
        debtor = Debtor()
        debtor.module.seat.credit_frozen_until = 110
        settle(debtor, year=105)
        event, = debtor.log
        self.assertEqual(debtor.module.seat.credit_frozen_until, 105 + SETTLEMENT_CREDIT_FREEZE_YEARS)
        self.assertTrue(event.facts["freeze_moved"])
        self.assertEqual(event.facts["frozen_before"], 110)


if __name__ == "__main__":
    unittest.main()

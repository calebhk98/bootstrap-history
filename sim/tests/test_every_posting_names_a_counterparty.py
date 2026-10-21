"""Complaint 382 step 1: every money posting names a counterparty or a named edge.

Money changes a purse only through `ledger.transfer`; where the other side is not an actor the simulation models, it is a
named edge, an account outside the actors in the purses' book (`state.actors.purses`). A new one-sided posting fails the
scan of the source below, and `ledger.transfer` against an edge is called on built purses. That all purses together plus
all edges together stay what they were over a year of a game is `test_every_posting_names_a_counterparty_scenario`."""
QUICK_TOPIC = True

import os
import re
import unittest

from sim.agents import ledger
from sim.engine.state import ActorsState

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCANNED = ("engine", "agents", "labour", "geography", "economy")
# the ledger itself, the purse's own methods, and the actors that delegate to the founder's purse
POSTING_WRITERS = {os.path.join("agents", "ledger.py"), os.path.join("engine", "state.py"),
                   os.path.join("agents", "household.py"), os.path.join("agents", "household_party.py")}
ONE_SIDED = re.compile(r"\.(credit|debit|add_capital|cost_capital|costCapital|reset_cash)\(")


def one_sided_postings():
    offenders = []
    for package in SCANNED:
        for folder, _dirs, files in os.walk(os.path.join(SIM_DIR, package)):
            for name in sorted(files):
                path = os.path.join(folder, name)
                relative = os.path.relpath(path, SIM_DIR)
                if not name.endswith(".py") or relative in POSTING_WRITERS:
                    continue
                with open(path, encoding="utf-8") as source:
                    for number, line in enumerate(source, 1):
                        if ONE_SIDED.search(line.split("#", 1)[0]):
                            offenders.append("%s:%d" % (relative, number))
    return offenders


class PostingTests(unittest.TestCase):
    def test_no_engine_or_agent_code_posts_money_to_one_side_only(self):
        self.assertEqual(one_sided_postings()[:20], [])

    def test_an_edge_takes_what_a_payer_loses_and_gives_what_a_payee_gains(self):
        state = ActorsState()
        payer = type("Purse", (), {"money": 10.0})()
        payer.debit = lambda amount, purpose: setattr(payer, "money", payer.money - amount)
        payer.credit = lambda amount, purpose: setattr(payer, "money", payer.money + amount)
        ledger.transfer(payer, state.edge("edge:test"), 4.0, "a payment")
        ledger.transfer(state.edge("edge:test"), payer, 1.0, "a refund")
        self.assertEqual(payer.money, 7.0)
        self.assertEqual(state.edge("edge:test").balance(), 3.0)

    def test_an_edge_keeps_the_volume_that_crossed_it(self):
        state = ActorsState()
        payer = type("Purse", (), {"money": 10.0})()
        payer.debit = lambda amount, purpose: setattr(payer, "money", payer.money - amount)
        payer.credit = lambda amount, purpose: setattr(payer, "money", payer.money + amount)
        ledger.transfer(payer, state.edge("edge:test"), 4.0, "a payment")
        ledger.transfer(state.edge("edge:test"), payer, 1.0, "a refund")
        self.assertEqual(state.edge("edge:test").volume(), 5.0)


if __name__ == "__main__":
    unittest.main()

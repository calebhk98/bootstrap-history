"""The actors module's side of the lenders: what the purse book answers about offers, loans and debts, and the year's sharing of
the pool's interest. Each is one method of the module over a stand-in purse book."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.actors.api import SetLenderOffers
from sim.actors.module import Actors
from sim.agents.api import EDGE_SAVERS, Business
from sim.ledger.api import NoteSeatCash
from sim.seats.api import SeatsSeat
from sim.tests import harness, module_harness  # noqa: F401  (harness isolates the home directory)


def actors_over(purses=None, cast=None, seat_ids=(), **world_fields):
    module = module_harness.build(Actors, views={"seat_list": {"joined": list(seat_ids), "playing": list(seat_ids)},
                                                 "seat_dealings": lambda seat_id: SeatsSeat(), "seat_business": lambda seat_id: Business()},
                                  world=SimpleNamespace(purses=purses, edge=lambda name: "edge " + name, **world_fields))
    if cast is not None:
        module.cast = lambda: cast
    return module


class PurseBookAnswers(unittest.TestCase):
    purses = SimpleNamespace(offers={EDGE_SAVERS: 7.0, "state": 3.0}, purse=lambda account: 5.0, deposit=lambda account: 0.25,
                             lent=lambda lender=None: 40.0 if lender is None else 9.0, debt=lambda account: 12.0)

    def test_the_offers_come_back_as_a_copy(self):
        module = actors_over(self.purses)
        offers = module.lender_offers_made()
        offers["x"] = 1.0
        self.assertEqual(self.purses.offers, {EDGE_SAVERS: 7.0, "state": 3.0})

    def test_cash_and_deposit_add_the_purse_to_what_the_pool_owes_the_account(self):
        self.assertEqual(actors_over(self.purses).cash_and_deposit("abbey"), 5.25)

    def test_loans_out_are_one_lenders_or_every_lenders(self):
        module = actors_over(self.purses)
        self.assertEqual((module.loans_out("state"), module.loans_out()), (9.0, 40.0))

    def test_the_debt_owed_is_the_books(self):
        self.assertEqual(actors_over(self.purses).debt_owed("state"), 12.0)

    def test_the_offers_command_sets_them_in_the_order_given(self):
        offers = {}
        module = actors_over(SimpleNamespace(set_offers=offers.update))
        module.set_lender_offers(SetLenderOffers((("b", 2.0), ("a", 1.0))))
        self.assertEqual(list(offers.items()), [("b", 2.0), ("a", 1.0)])


class SettleLenderInterest(unittest.TestCase):
    def settle(self, received, seat_ids=()):
        income, shared = [], []
        abbey = SimpleNamespace(note_income=lambda purpose, amount: income.append(("abbey", purpose, amount)))
        cast = SimpleNamespace(actors={"abbey": abbey})
        module = actors_over(SimpleNamespace(settle_interest=lambda: received), cast, seat_ids)
        with mock.patch("sim.actors.lending.payroll", SimpleNamespace(pay_savers=lambda registry, edge, amount: shared.append((edge, amount)))):
            module.settle_lender_interest()
        self.sent = module_harness.sent(module)
        return income, shared

    def test_the_interest_the_pool_holds_reaches_each_lender_and_the_savers(self):
        self.assertEqual(self.settle({"abbey": 12.0, EDGE_SAVERS: 7.0}),
                         ([("abbey", "interest_on_lending", 12.0)], [("edge " + EDGE_SAVERS, 7.0)]))

    def test_a_seat_that_lent_has_the_interest_entered_in_its_cash_book(self):
        self.settle({"seat:a": 4.0}, ("seat:a",))
        self.assertEqual(self.sent, [NoteSeatCash("seat:a", 1.0, 4.0, "interest_on_lending")])

    def test_no_savers_part_shares_nothing_and_an_unknown_lender_is_skipped(self):
        self.assertEqual(self.settle({"edge:other": 3.0}), ([], []))


if __name__ == "__main__":
    unittest.main()

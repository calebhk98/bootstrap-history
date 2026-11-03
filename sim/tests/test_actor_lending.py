"""The actors module's side of the lenders: what the purse book answers about offers, loans and debts, and the year's sharing of
the pool's interest. Each is one method of the module over a stand-in purse book."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors.api import SetLenderOffers
from sim.actors.module import Actors
from sim.ledger.api import NoteSeatCash
from sim.seats.api import SeatsSeat
from sim.tests import harness, module_harness  # noqa: F401  (harness isolates the home directory)


def actors_over(purses=None, cast=None, seat_ids=(), views=None, **world_fields):
    module = module_harness.build(Actors, views={"seat_list": {"joined": list(seat_ids), "playing": list(seat_ids)},
                                                 "seat_dealings": lambda seat_id: SeatsSeat(), **(views or {})},
                                  world=SimpleNamespace(purses=purses, edge=lambda name: "edge " + name, **world_fields))
    if cast is not None:
        module.cast = lambda: cast
    return module


class PurseBookAnswers(unittest.TestCase):
    purses = SimpleNamespace(offers={"firm:1": 7.0, "state": 3.0}, purse=lambda account: 5.0, deposit=lambda account: 0.25,
                             lent=lambda lender=None: 40.0 if lender is None else 9.0, debt=lambda account: 12.0)

    def test_the_offers_come_back_as_a_copy(self):
        module = actors_over(self.purses)
        offers = module.lender_offers_made()
        offers["x"] = 1.0
        self.assertEqual(self.purses.offers, {"firm:1": 7.0, "state": 3.0})

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
        income = []
        abbey = SimpleNamespace(payments=SimpleNamespace(note_income=lambda purpose, amount: income.append(("abbey", purpose, amount))))
        cast = SimpleNamespace(actors={"abbey": abbey})
        module = actors_over(SimpleNamespace(settle_interest=lambda: received), cast, seat_ids)
        module.settle_lender_interest()
        self.sent = module_harness.sent(module)
        return income

    def test_the_interest_the_pool_holds_reaches_each_actor_that_lent(self):
        self.assertEqual(self.settle({"abbey": 12.0}), [("abbey", "interest_on_lending", 12.0)])

    def test_a_seat_that_lent_has_the_interest_entered_in_its_cash_book(self):
        self.settle({"seat:a": 4.0}, ("seat:a",))
        self.assertEqual(self.sent, [NoteSeatCash("seat:a", 1.0, 4.0, "interest_on_lending")])

    def test_an_economy_lender_was_paid_in_the_book_and_enters_no_actors_income(self):
        self.assertEqual(self.settle({"cohort:a": 3.0}), [])


class LendersForADraw(unittest.TestCase):
    listing = {"currency": "unit", "coin_per_unit": 2.0, "lenders": [("cohort:a", 10.0, 10.0, 0.04), ("bank:b", 5.0, 5.0, 0.09)]}

    def lenders(self, account, rate, listing=(True, listing)):
        actor = SimpleNamespace(rate_on_loan=lambda world, amount: rate)
        module = actors_over(views={"agent_lender_listing": lambda: listing})
        module.parts.cast.actor_world = lambda: SimpleNamespace(registry=SimpleNamespace(actors={"firm:1": actor}))
        return module.lenders_for_draw(account, 100.0)

    def test_only_lenders_asking_no_more_than_the_draws_rate_are_offered(self):
        unit, per_unit, rows = self.lenders("firm:1", 0.05)
        self.assertEqual((unit, per_unit, [row[0] for row in rows]), ("unit", 2.0, ["cohort:a"]))

    def test_an_account_no_actor_stands_behind_is_offered_every_lender(self):
        self.assertEqual([row[0] for row in self.lenders("seat:a", 0.0)[2]], ["cohort:a", "bank:b"])

    def test_no_lenders_listed_or_an_economy_still_opening_offers_none(self):
        self.assertIsNone(self.lenders("firm:1", 0.05, (False, None)))
        self.assertIsNone(self.lenders("firm:1", 0.05, (True, dict(self.listing, lenders=[]))))


if __name__ == "__main__":
    unittest.main()

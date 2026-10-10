"""The actors' purses and the economy's agents keep their money in one book: adopting the economy's book moves the
purses over, the economy's year runs with the actors' accounts in it, and each owner saves only its own currency."""

QUICK_TOPIC = True

import unittest

from sim.agents import ledger
from sim.agents.api import ActorRecord, ActorsState
from sim.agents.firm import Firm
from sim.agents.purses import COIN, Purses
from sim.economy import api as economy_api
from sim.tests import economy_fixture


def actors_with_money():
    state = ActorsState()
    firm = Firm("firm:a", ActorRecord(kind="firm", money=100.0))
    other = Firm("firm:b", ActorRecord(kind="firm"))
    for actor in (firm, other):
        actor.attach(state.purses)
    ledger.transfer(firm, other, 130.0, "buy")     # draws on the facility for 30
    return state, firm, other


class SharedBook(unittest.TestCase):
    def test_adopting_the_economys_book_moves_the_accounts_over(self):
        state, firm, other = actors_with_money()
        economy, _outcomes = economy_fixture.run(years=1)
        book = economy_api.economy_book(economy)
        state.purses.adopt_book(book)
        self.assertIs(state.purses.book, book)
        self.assertEqual(book.balance("firm:b", COIN), 130.0)
        self.assertEqual(firm.money, -30.0)
        self.assertEqual(state.purses.debt("firm:a"), 30.0)

    def test_the_economys_year_runs_with_the_actors_accounts_in_the_book(self):
        state, firm, other = actors_with_money()
        economy = economy_fixture.run(years=1)[0]
        state.purses.adopt_book(economy_api.economy_book(economy))
        for _year in range(2):
            economy.step(economy_fixture.quiet_year(economy.setup))
        self.assertEqual(state.purses.purse("firm:b"), 130.0)
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())

    def test_each_owner_saves_only_its_own_currency(self):
        state, _firm, _other = actors_with_money()
        economy = economy_fixture.run(years=1)[0]
        state.purses.adopt_book(economy_api.economy_book(economy))
        mine = state.purses.to_canon_dict()["book"]["money"]
        theirs = economy_api.export_record(economy, (COIN,))["book"]["money"]
        self.assertTrue(all(set(held) == {COIN} for held in mine.values()))
        self.assertTrue(all(COIN not in held for held in theirs.values()))
        self.assertIn("firm:b", mine)
        self.assertNotIn("firm:b", theirs)

    def test_a_loaded_pair_of_records_joins_again(self):
        state, _firm, _other = actors_with_money()
        economy = economy_fixture.run(years=1)[0]
        state.purses.adopt_book(economy_api.economy_book(economy))
        purses_record = state.purses.to_canon_dict()
        economy_record = economy_api.export_record(economy, (COIN,))
        again = Purses.from_record(purses_record)
        resumed = economy_api.economy_from_record(economy.setup, economy_record)
        again.adopt_book(economy_api.economy_book(resumed))
        self.assertEqual(again.purse("firm:b"), 130.0)
        self.assertEqual(again.debt("firm:a"), 30.0)
        self.assertEqual(economy_api.economy_book(resumed).money_supply(economy.setup.currency_id),
                         economy_api.economy_book(economy).money_supply(economy.setup.currency_id))


if __name__ == "__main__":
    unittest.main()

"""A merchant never posts more carriage than its purse holds: a float sliver left over on one route must not be
handed back as cash for the next (Rome games crashed with InsufficientFunds of a few 1e-14 in dispatch_merchants)."""
QUICK_TOPIC = True

import unittest

from sim.book import Book
from sim.economy import merchants
from sim.economy.types import EDGE_MINT, GoodSpec, Transfer
from sim.tests.test_economy_merchants import SPECS, merchant, world


class PurseResidue(unittest.TestCase):
    def test_a_merchant_with_no_cash_pays_nothing_and_its_postings_do_not_overdraw(self):
        carriage, _map, area_a, area_b = world()
        # on the fish route crew pay plus carrier cost, rounded, comes to a hair more than the fee
        specs = {"fish": GoodSpec("fish", 1496.0485584697803, 0.0, 0.0, "food"), "salt": SPECS["salt"]}
        who = merchant()
        who.routes = {("fish", "a"): ("b", area_b["salt"]), ("salt", "b"): ("a", area_a["salt"])}
        crew = merchants.CrewHire(lambda source, destination: (("carter|a", 1.0),), None, {"carter|a": 0.19976567904521148})
        result = merchants.dispatch(who, (), carriage, specs, "coin", 0.0, {("fish", "a"): 10.0, ("salt", "b"): 10.0},
                                    crew=crew, carrier_money=lambda source, destination: 10.0 if source == "a" else 0.0)
        self.assertEqual(sum(transfer.amount for transfer in result.transfers), 0.0)

    def test_a_purse_spent_to_the_last_ulp_posts_without_error(self):
        carriage, _map, area_a, area_b = world()
        who = merchant()
        who.routes = {("salt", "a"): ("b", area_b["salt"])}
        cash = 3.3000000000000003
        book = Book()
        book.transfer_many([Transfer(EDGE_MINT, who.agent_id, "coin", cash, "seed")])
        book.move_many([])
        result = merchants.dispatch(who, (), carriage, SPECS, "coin", book.balance(who.agent_id, "coin"),
                                    {("salt", "a"): 1000.0})
        book.transfer_many(result.transfers)
        self.assertGreaterEqual(book.balance(who.agent_id, "coin"), 0.0)


if __name__ == "__main__":
    unittest.main()

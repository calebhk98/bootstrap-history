"""The block reads of the book, the ledger, the setup and the area map, each against the per-item read it replaces, on written-out inputs."""
QUICK_TOPIC = True

import math
import unittest
from types import SimpleNamespace

import numpy

from sim.book import Book, GoodsMove, Transfer
from sim.compiled_tables.ids import IdTable
from sim.economy.market_areas import AreaMap
from sim.economy.setup_countries import country_by_tile
from sim.economy.year_accounts_columns import column, row_columns, sum_across, summed_by_key
from sim.economy.year_ledger_plain import plain_by_agent


def stocked_book() -> Book:
    book = Book()
    for agent, good, tile, quantity in (("b", "wheat", "t2", 3.0), ("b", "iron", "t1", 2.0), ("a", "wheat", "t1", 5.0),
                                        ("b", "wheat", "t1", 1.5), ("a", "iron", "t1", 4.0), ("b", "iron", "t1", 0.5)):
        book.move(GoodsMove("edge:world", agent, good, tile, quantity, "start"))
    book.move(GoodsMove("a", "edge:world", "iron", "t1", 4.0, "use"))       # leaves a slot at zero
    book.transfer(Transfer("edge:world", "a", "coin", 7.0, "start"))
    book.transfer(Transfer("edge:world", "a", "silver", 2.0, "start"))
    book.transfer(Transfer("a", "edge:world", "silver", 2.0, "back"))        # a balance written and back at zero
    return book


class IdTableBlockTests(unittest.TestCase):
    def test_numbers_if_known_lists_the_numbers_or_none_for_a_new_name(self):
        ids = IdTable("good", ["wheat", "iron"])
        self.assertEqual((ids.numbers_if_known(["wheat", "iron", "wheat"]), ids.numbers_if_known(["wheat", "zinc"])), ([1, 0, 1], None))

    def test_name_order_and_rank_follow_the_names_and_grow_with_the_table(self):
        ids = IdTable.from_state("good", ["wheat", "iron", "brass"])
        before = (ids.name_order().tolist(), ids.name_rank().tolist())
        ids.admit(["copper"])
        self.assertEqual((before, ids.name_order().tolist(), ids.name_rank().tolist()),
                         (([2, 1, 0], [2, 1, 0]), [2, 3, 1, 0], [3, 2, 0, 1]))


class BookHoldingsTests(unittest.TestCase):
    def test_goods_held_many_equals_goods_held_agent_by_agent(self):
        book = stocked_book()
        agents = ["b", "nobody", "a", "b"]
        self.assertEqual(book.goods_held_many(agents), [book.goods_held(agent) for agent in agents])

    def test_goods_held_is_in_name_order_and_leaves_out_zeros(self):
        held = stocked_book().goods_held("b")
        self.assertEqual([(good, list(by_tile.items())) for good, by_tile in held.items()],
                         [("iron", [("t1", 2.5)]), ("wheat", [("t1", 1.5), ("t2", 3.0)])])

    def test_goods_of_keeps_the_zero_slot_in_the_order_the_slots_were_made(self):
        self.assertEqual(stocked_book().goods_of("a"), {"wheat": {"t1": 5.0}, "iron": {"t1": 0.0}})

    def test_holdings_money_is_the_nonzero_balances_in_currency_name_order(self):
        book = stocked_book()
        book.transfer(Transfer("edge:world", "a", "aurum", 1.0, "start"))
        self.assertEqual(list(book.holdings("a")["money"].items()), [("aurum", 1.0), ("coin", 7.0)])

    def test_balance_by_agent_equals_balance_for_each_agent(self):
        book = stocked_book()
        self.assertEqual(book.balance_by_agent(["a", "b", "nobody"], "coin"),
                         {agent: book.balance(agent, "coin") for agent in ["a", "b", "nobody"]})


class BookFlowColumnTests(unittest.TestCase):
    def test_flow_by_purpose_and_prefix_equal_the_flows_dictionary(self):
        book = Book()
        for good, purpose, quantity in (("wheat", "input", 2.0), ("wheat", "state stores used", 1.25), ("iron", "state wages", 0.1),
                                        ("iron", "state stores used", 0.2), ("iron", "consumption", 4.0), ("wheat", "consumption", 1.0)):
            book.move(GoodsMove("edge:world", "a", good, "t", quantity, purpose))
        flows = book.goods_flows()
        goods = ["iron", "wheat", "unseen"]
        self.assertEqual(book.flow_by_purpose("consumption", goods), [flows.get(good, {}).get("consumption", 0.0) for good in goods])
        self.assertEqual(book.flow_by_prefix("state ", goods),
                         [math.fsum(q for purpose, q in flows.get(good, {}).items() if purpose.startswith("state ")) for good in goods])

    def test_flow_by_purpose_of_a_purpose_never_posted_is_zero(self):
        self.assertEqual(stocked_book().flow_by_purpose("never posted", ["wheat"]), [0.0])


class LedgerPlainTests(unittest.TestCase):
    def test_plain_by_agent_gives_members_in_order_with_their_rows_in_row_order(self):
        names_of_subs = lambda subkeys, extras: ["good%d" % subkey for subkey in subkeys]       # noqa: E731
        plain = plain_by_agent(numpy.array([2, 0, 1]), ["c", "a", "b"], numpy.array([0, 2, 0, 3, 2, 0]), numpy.array([5, 6, 7, 8, 9, 5]),
                               numpy.zeros(6, dtype=numpy.int64), numpy.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]), names_of_subs)
        self.assertEqual((list(plain), plain), (["c", "a", "b"], {"c": {"good6": 2.0, "good9": 5.0}, "a": {"good5": 6.0, "good7": 3.0}, "b": {}}))


class AccountColumnTests(unittest.TestCase):
    def test_summed_by_key_adds_in_the_order_given_like_a_running_dictionary_sum(self):
        keys, values = ["a", "b", "a", "a", "b"], [1e16, 0.1, 1.0, -1e16, 0.2]
        running = {}
        for key, value in zip(keys, values):
            running[key] = running.get(key, 0.0) + value
        self.assertEqual(summed_by_key(keys, values), dict(sorted(running.items())))

    def test_column_reads_zero_for_a_missing_key(self):
        self.assertEqual(column({"a": 2.0}, ["a", "b"]), [2.0, 0.0])

    def test_row_columns_concatenates_the_agents_rows_in_order(self):
        self.assertEqual(row_columns({"x": {"a": 1.0}, "y": {"b": 2.0, "a": 3.0}}, ["y", "z", "x"]), (["b", "a", "a"], [2.0, 3.0, 1.0]))

    def test_sum_across_is_the_exact_sum_per_position_and_zeros_without_columns(self):
        self.assertEqual((sum_across([[0.1, 1.0], [0.2, 2.0], [0.3, 3.0]], 2), sum_across([], 3)),
                         ([math.fsum([0.1, 0.2, 0.3]), 6.0], [0.0] * 3))


class CountryTests(unittest.TestCase):
    def test_country_by_tile_is_the_owner_else_the_tiles_country_else_the_setups(self):
        setup = SimpleNamespace(civ_id="rome", tiles={"a": SimpleNamespace(country=""), "b": SimpleNamespace(country="gaul"),
                                                      "c": SimpleNamespace(country="gaul")},
                                tile_owners={"c": {"owner": "rome"}, "z": {"owner": "elsewhere"}, "a": {}})
        self.assertEqual(country_by_tile(setup), {"a": "rome", "b": "gaul", "c": "rome"})


class AreaTileTests(unittest.TestCase):
    def test_areas_on_tile_equals_area_of_for_every_good_with_an_area_there(self):
        areas = AreaMap.__new__(AreaMap)
        areas._bucket_of_good = {"wheat": "low", "gold": "high", "salt": "low"}
        areas._area_of_tile = {"low": {"t1": "low:1", "t2": "low:2"}, "high": {"t1": "high:1"}}
        areas._areas_on_tile = {}
        self.assertEqual((areas.areas_on_tile("t1"), areas.areas_on_tile("t2"), areas.areas_on_tile("t3")),
                         ({good: areas.area_of(good, "t1") for good in ("wheat", "gold", "salt")},
                          {"wheat": "low:2", "salt": "low:2"}, {}))


if __name__ == "__main__":
    unittest.main()

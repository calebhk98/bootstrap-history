"""Numba port item 7, wear and spoilage: `year_close.wear_and_spoilage` reads only the goods that spoil or wear, where the old
function listed every holding of every agent. Each book ends the same as the one the old function (copied here) works on,
on the random economies of year_close_fixture. No game."""

QUICK_TOPIC = True

import copy
import types
import unittest
from typing import Dict, Tuple

from sim.economy import carriage_wear, inventory, metal_stock, year_close
from sim.economy.types import CurrencySpec, is_edge
from sim.tests.year_close_fixture import MONEY, economy_of


def old_wear_and_spoilage(setup, record, durable_users=()):
    book = record.book
    holdings: Dict[Tuple[str, str, str], float] = {}
    for agent in book.agents():
        if is_edge(agent):
            continue
        held = book.goods_of(agent)
        for good in sorted(held):
            by_tile = held[good]
            for tile in sorted(by_tile):
                if by_tile[tile] > 0.0:
                    holdings[(agent, good, tile)] = by_tile[tile]
    book.move_many(inventory.spoilage_moves(holdings, setup.specs))
    fleets = {carriage_wear.account(merchant_id) for merchant_id in record.merchants}
    book.move_many(inventory.wear_moves(holdings, setup.specs, set(record.cohorts) | set(durable_users) | fleets))
    cash = {agent: book.balance(agent, record.currency.currency_id) for agent in book.agents() if not is_edge(agent)}
    book.transfer_many(metal_stock.yearly_wear(cash, record.currency))


def stocks_of(book):
    return {(agent, good, tile): quantity for agent in book.agents() for good, by_tile in book.goods_of(agent).items()
            for tile, quantity in by_tile.items() if quantity != 0.0}


class WearAndSpoilageIsTheOldPass(unittest.TestCase):

    def test_random_books(self):
        for seed in range(6):
            setup, record, _view, _ledger, _area_map = economy_of(seed, producer_count=50)
            record.merchants = {}
            record.currency = CurrencySpec(MONEY, "struck_coin", None, 0.0, None) if seed % 2 else types.SimpleNamespace(regime="fiat", currency_id=MONEY)
            old_record = copy.deepcopy(record)
            old_wear_and_spoilage(setup, old_record, ("producer:003",))
            year_close.wear_and_spoilage(setup, record, ("producer:003",))
            self.assertEqual(stocks_of(record.book), stocks_of(old_record.book))
            self.assertEqual(record.book.numbering_state(), old_record.book.numbering_state())
            for edge in ("edge:spoilage", "edge:consumption", "edge:wear"):
                self.assertEqual(record.book.edge_volume(edge, MONEY), old_record.book.edge_volume(edge, MONEY))
                for good in record.book.gross_goods():
                    self.assertEqual(record.book.edge_goods_net(edge, good), old_record.book.edge_goods_net(edge, good))
            for agent in record.book.agents():
                self.assertEqual(record.book.balance(agent, MONEY), old_record.book.balance(agent, MONEY))
            self.assertNotEqual(stocks_of(record.book), stocks_of(copy.deepcopy(economy_of(seed, producer_count=50)[1].book)))


if __name__ == "__main__":
    unittest.main()

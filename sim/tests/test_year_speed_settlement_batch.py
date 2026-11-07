"""Numba port, settlement of a good's markets together (`settlement.settle_goods_many`): several markets of one good settled in
one kernel call and posted once leave the book, the year ledger and each market's own figures as the per-pair reference
settlement (settlement_reference.py) run market after market on one book does, on random pairings that share agents, short
purses and short stocks, so a market sees what the earlier ones spent. No game.

A relative tolerance is needed because the kernel sums left to right and the batch is posted summed per agent, where the
reference posted pair by pair and market by market."""

QUICK_TOPIC = True

import random
import unittest

from sim.book import Book
from sim.economy import settlement
from sim.economy.types import Pairing
from sim.economy.year_ledger import YearLedger

from . import settlement_reference
from .test_year_speed_settlement import FakeResult, TOLERANCE, close, random_pairing, random_world, snapshot, snapshot_copy


def without_noise(by_agent):
    """The entries of a per-agent map that are not rounding noise: a purse or stock one market leaves at 1e-15 of what it had
    is spent or not by the next market depending on the order its sums were added in, which no tolerance can close."""
    return {agent: figure for agent, figure in by_agent.items()
            if max(abs(each) for each in (figure if isinstance(figure, tuple) else (figure,))) > 1e-12}


def pruned(figures):
    """A nested map without its rounding-noise numbers and the maps that empties."""
    if isinstance(figures, dict):
        kept = {key: pruned(value) for key, value in figures.items()}
        return {key: value for key, value in kept.items() if value not in ({}, None)}
    if isinstance(figures, tuple):
        return tuple(pruned(each) for each in figures)
    return figures if abs(figures) > 1e-12 else None


class SeveralMarketsSettleAsOneAfterAnother(unittest.TestCase):

    def test_random_batches_of_goods_markets(self):
        rng = random.Random(21)
        for _round in range(150):
            agents, book = random_world(rng)
            old_book = Book()
            old_book.__dict__.update(snapshot_copy(book))
            pairings = [random_pairing(rng, agents) for _ in range(rng.randint(1, 5))]
            if rng.random() < 0.3:
                pairings.insert(rng.randint(0, len(pairings)), Pairing((), (), (), (), (), ()))
            accounts = frozenset(rng.sample(agents, 1))
            old_ledger, new_ledger = YearLedger(), YearLedger()
            old_ledger.import_accounts = new_ledger.import_accounts = accounts
            old_ledger.export_accounts = new_ledger.export_accounts = accounts
            plant_goods = {agent: {"grain"} for agent in rng.sample(agents, 2)}
            olds = []
            for pairing in pairings:
                old = settlement_reference.settle_goods(old_book, FakeResult(pairing))
                old_ledger.note_postings(old.postings, "sales")
                old_ledger.note_plant_purchases(old.postings, "grain", plant_goods)
                olds.append(old)
            news = settlement.settle_goods_many(book, [FakeResult(pairing) for pairing in pairings], accounts, accounts)
            self.assertEqual(len(news), len(pairings))
            for old, new in zip(olds, news):
                new_ledger.note_settlement(new, "sales", plant_goods)
                close(without_noise(old.bought_by_buyer()), without_noise(new.bought_by_buyer()))
                close(without_noise(old.buyer_money), without_noise(new.buyer_money))
                moved = sum(getattr(posting, "quantity", 0.0) for posting in old.postings if hasattr(posting, "giver"))
                self.assertAlmostEqual(moved, new.delivered, delta=TOLERANCE * max(1.0, moved))
            close(pruned(snapshot(old_book)), pruned(snapshot(book)))
            for name in ("money_out", "sales_in", "received", "sold", "pending_mint_takes", "imports_paid",
                         "exports_received", "plant_spend"):
                close(pruned(getattr(old_ledger, name)), pruned(getattr(new_ledger, name)), name)

    def test_no_markets_settle_nothing(self):
        self.assertEqual(settlement.settle_goods_many(Book(), []), [])
        news = settlement.settle_goods_many(Book(), [FakeResult(Pairing((), (), (), (), (), ()))])
        self.assertEqual(news[0].agents, [])
        self.assertEqual(news[0].delivered, 0.0)


if __name__ == "__main__":
    unittest.main()

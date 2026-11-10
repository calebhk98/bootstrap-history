"""Numba port, settlement: a goods or labour market settled by the kernel (`settlement.settle_goods`, `settle_labour`) and
noted in the year ledger (`YearLedger.note_settlement`) leaves the book and the ledger as the per-pair settlement it replaced
(settlement_reference.py, then `note_postings` and `note_plant_purchases` of its postings) does, on random pairings with
short purses, short stocks, edge accounts and negative asks; no game.

A relative tolerance is needed because the kernel sums each agent's pairs left to right and the book is posted summed per
agent, where the old path posted pair by pair."""

QUICK_TOPIC = True

import random
from collections.abc import Mapping
import unittest

from sim.book import Book
from sim.economy import settlement
from sim.economy.types import EDGE_EXTERNAL, EDGE_MINT, EDGE_PRODUCTION, Pairing, Transfer
from sim.economy.year_ledger import YearLedger
from sim.economy.types import GoodsMove

from . import settlement_reference

TOLERANCE = 1e-9


def random_world(rng):
    agents = ["a%d" % index for index in range(rng.randint(2, 7))]
    book = Book()
    for agent in agents:
        book.transfer(Transfer(EDGE_MINT, agent, "coin", rng.choice([0.0, rng.uniform(1, 50), rng.uniform(100, 5000)]), "start"))
        for tile in ("t1", "t2"):
            book.move(GoodsMove(EDGE_PRODUCTION, agent, "grain", tile, rng.choice([0.0, rng.uniform(1, 20), rng.uniform(50, 400)]), "start"))
    book.transfer(Transfer(EDGE_MINT, EDGE_EXTERNAL + ":far", "coin", 0.0, "start"))
    return agents, book


def random_pairing(rng, agents):
    buyer_pool = agents + [EDGE_MINT, EDGE_EXTERNAL + ":far"]
    seller_pool = agents + [EDGE_PRODUCTION, EDGE_EXTERNAL + ":far"]
    buyers = tuple((rng.choice(buyer_pool), rng.choice(["t1", "t2", "t3", ""] if rng.random() < 0.1 else ["t1", "t2", "t3"]))
                   for _ in range(rng.randint(1, 6)))
    sellers = tuple((rng.choice(seller_pool), rng.choice(["t1", "t2"])) for _ in range(rng.randint(1, 5)))
    asks = tuple(rng.choice([rng.uniform(0.1, 9.0), rng.uniform(0.1, 9.0), 0.0, -rng.uniform(0.1, 2.0)]) for _ in sellers)
    pairs = [(rng.randrange(len(buyers)), rng.randrange(len(sellers)), rng.uniform(0.0, 120.0)) for _ in range(rng.randint(1, 14))]
    return Pairing(buyers, sellers, asks, tuple(pair[0] for pair in pairs), tuple(pair[1] for pair in pairs),
                   tuple(pair[2] for pair in pairs))


def snapshot(book):
    record = book.to_record()
    return {"money": record["money"], "goods": record["goods"], "gross_money": record["gross_money"],
            "gross_goods": record["gross_goods"],
            "edge_money": (record["edge_money_volume"], record["edge_money_net"]),
            "edge_goods": (record["edge_goods_volume"], record["edge_goods_net"])}


def close(left, right, path=""):
    """Every number in two nested structures agrees within TOLERANCE of the larger (or of one, near zero)."""
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        keys = {key for key, value in list(left.items()) + list(right.items()) if abs(value if isinstance(value, float) else 1.0) > TOLERANCE
                or isinstance(value, (Mapping, tuple))}
        for key in keys:
            close(left.get(key, 0.0), right.get(key, 0.0), "%s/%s" % (path, key))
        return
    if isinstance(left, tuple):
        for index, (one, other) in enumerate(zip(left, right)):
            close(one, other, "%s/%d" % (path, index))
        return
    assert abs(left - right) <= TOLERANCE * max(1.0, abs(left), abs(right)), (path, left, right)


class FakeResult:
    def __init__(self, pairing):
        self.fills, self.currency, self.good, self.pairing = (), "coin", "grain", pairing


class SettlementKernelAgreesWithThePerPairSettlement(unittest.TestCase):

    def test_random_goods_markets(self):
        rng = random.Random(11)
        for _round in range(250):
            agents, book = random_world(rng)
            old_book = Book()
            old_book.__dict__.update({name: value for name, value in snapshot_copy(book).items()})
            pairing = random_pairing(rng, agents)
            import_accounts = frozenset(rng.sample(agents, 1))
            export_accounts = frozenset(rng.sample(agents, 1))
            plant_goods = {agent: {"grain"} for agent in rng.sample(agents, 2)}
            old_ledger, new_ledger = YearLedger(), YearLedger()
            old_ledger.import_accounts = new_ledger.import_accounts = import_accounts
            old_ledger.export_accounts = new_ledger.export_accounts = export_accounts
            result = FakeResult(pairing)
            old = settlement_reference.settle_goods(old_book, result)
            old_ledger.note_postings(old.postings, "sales")
            old_ledger.note_plant_purchases(old.postings, "grain", plant_goods)
            new = settlement.settle_goods(book, result, import_accounts, export_accounts)
            new_ledger.note_settlement(new, "sales", plant_goods)
            close(snapshot(old_book), snapshot(book))
            for name in ("money_out", "sales_in", "received", "sold", "pending_mint_takes", "imports_paid",
                         "exports_received", "plant_spend"):
                close(getattr(old_ledger, name), getattr(new_ledger, name), name)
            close(old.bought_by_buyer(), new.bought_by_buyer())
            close(old.buyer_money, new.buyer_money)
            moved = sum(move.quantity for move in old.postings if isinstance(move, GoodsMove))
            self.assertAlmostEqual(moved, new.delivered, delta=TOLERANCE * max(1.0, moved))

    def test_random_labour_markets(self):
        rng = random.Random(12)
        for _round in range(120):
            agents, book = random_world(rng)
            old_book = Book()
            old_book.__dict__.update(snapshot_copy(book))
            pairing = random_pairing(rng, agents)
            pairing = Pairing(pairing.buyers, pairing.sellers, tuple(abs(ask) for ask in pairing.asks), pairing.buyer_index,
                              pairing.seller_index, pairing.quantity)
            result = FakeLabour(pairing)
            old = settlement_reference._settle(old_book, (), "coin", "smith", "wages for smith", False, pairing=pairing)
            old_ledger, new_ledger = YearLedger(), YearLedger()
            old_ledger.note_postings(old.postings, "wages")
            new = settlement._settle(book, (), "coin", "smith", "wages for smith", False, pairing=pairing)
            new_ledger.note_settlement(new, "wages")
            close(snapshot(old_book), snapshot(book))
            for name in ("money_out", "wages_in", "imports_paid", "exports_received"):
                close(getattr(old_ledger, name), getattr(new_ledger, name), name)
            paid_by, paid_to = {}, {}
            for posting in old.postings:
                paid_by[posting.payer] = paid_by.get(posting.payer, 0.0) + posting.amount
                paid_to[posting.payee] = paid_to.get(posting.payee, 0.0) + posting.amount
            close(paid_by, new.paid_by)
            close(paid_to, new.paid_to)
            self.assertEqual(result.pairing, pairing)

    def test_postings_rebuilt_from_the_arrays_match_the_old_ones(self):
        rng = random.Random(13)
        for _round in range(80):
            agents, book = random_world(rng)
            old_book = Book()
            old_book.__dict__.update(snapshot_copy(book))
            pairing = random_pairing(rng, agents)
            old = [posting for posting in settlement_reference.settle_goods(old_book, FakeResult(pairing)).postings
                   if getattr(posting, "amount", getattr(posting, "quantity", 0.0)) > 0.0]
            new = settlement.settle_goods(book, FakeResult(pairing)).postings
            self.assertEqual(len(old), len(new))
            for before, after in zip(sorted(old, key=repr_key), sorted(new, key=repr_key)):
                self.assertEqual(type(before), type(after))
                self.assertEqual(before.purpose, after.purpose)
                amount = getattr(before, "amount", None) if isinstance(before, Transfer) else before.quantity
                other = getattr(after, "amount", None) if isinstance(after, Transfer) else after.quantity
                self.assertAlmostEqual(amount, other, delta=TOLERANCE * max(1.0, amount))


class FakeLabour:
    def __init__(self, pairing):
        self.pairing = pairing


def repr_key(posting):
    if isinstance(posting, Transfer):
        return (0, posting.payer, posting.payee)
    return (1, posting.giver, posting.receiver, posting.tile)


def snapshot_copy(book):
    """A second book with the first one's entries and records, to settle with the reference."""
    import copy
    return {name: copy.deepcopy(value) for name, value in book.__dict__.items()}


if __name__ == "__main__":
    unittest.main()

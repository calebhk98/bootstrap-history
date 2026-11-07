"""The array book (sim/book.py) against the dictionary book it replaced (book_reference.py): the same postings give the
same balances, stocks, flows, refusals and save file, to the last digit (the sums are done in the same order)."""

QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.book import Book, BookError, GoodsMove, Transfer
from sim.tests.book_reference import ReferenceBook

AGENTS = ["a1", "a2", "a3", "a4", "edge:mint", "edge:world"]
TILES = ["t1", "t2", "t3"]
GOODS = ["grain", "iron"]
CURRENCIES = ["coin", "bullion"]


def pair_of_books(rng, rounds=12):
    """Two books, the array one and the reference, after the same random postings."""
    books = (Book(), ReferenceBook())
    for book in books:
        for agent in AGENTS[:4]:
            book.transfer(Transfer("edge:mint", agent, "coin", 50.0, "start"))
            book.move(GoodsMove("edge:world", agent, "grain", "t1", 20.0, "start"))
    for _ in range(rounds * 3):
        kind = rng.choice(["transfer", "move", "post"])
        transfers = [Transfer(rng.choice(AGENTS), rng.choice(AGENTS), rng.choice(CURRENCIES), rng.uniform(0.0, 40.0), "x")
                     for _ in range(rng.randint(1, 3))]
        moves = [GoodsMove(rng.choice(AGENTS), rng.choice(AGENTS), rng.choice(GOODS), rng.choice(TILES), rng.uniform(0.0, 9.0), "y")
                 for _ in range(rng.randint(1, 3))]
        for book in books:
            try:
                if kind == "transfer":
                    book.transfer_many(transfers)
                elif kind == "move":
                    book.move_many(moves)
                else:
                    book.post(transfers, moves)
            except BookError:
                pass
    return books


def settled_arguments(rng):
    agents = rng.sample(AGENTS, 4)
    keys = list(dict.fromkeys((rng.choice(AGENTS), rng.choice(TILES)) for _ in range(5)))
    count = len(agents)
    return dict(currency="coin", purpose="sale", item="grain", agents=agents,
                paid=[rng.choice([0.0, rng.uniform(0.0, 60.0)]) for _ in range(count)],
                received=[rng.choice([0.0, rng.uniform(0.0, 60.0)]) for _ in range(count)], keys=keys,
                given=[rng.choice([0.0, rng.uniform(0.0, 8.0)]) for _ in keys],
                taken=[rng.choice([0.0, rng.uniform(0.0, 8.0)]) for _ in keys])


class ArrayBookAgreesWithTheDictionaryBook(unittest.TestCase):
    def test_postings_give_the_same_record_and_reads(self):
        rng = random.Random(3)
        for _ in range(60):
            new, old = pair_of_books(rng)
            self.assertEqual(new.to_record(), old.to_record())
            for agent in AGENTS + ["nobody"]:
                self.assertEqual(new.knows(agent), old.knows(agent))
                self.assertEqual(new.holdings(agent), old.holdings(agent))
                self.assertEqual(new.goods_held(agent), old.goods_held(agent))
                for currency in CURRENCIES:
                    self.assertEqual(new.balance(agent, currency), old.balance(agent, currency))
                for good in GOODS:
                    for tile in TILES:
                        self.assertEqual(new.stock(agent, good, tile), old.stock(agent, good, tile))
            self.assertEqual(new.agents(), old.agents())
            self.assertEqual(new.currencies(), old.currencies())
            for currency in CURRENCIES:
                self.assertEqual(new.money_supply(currency), old.money_supply(currency))
                self.assertEqual(new.total(currency), old.total(currency))
            for good in GOODS:
                self.assertEqual(new.goods_total(good), old.goods_total(good))
                self.assertEqual(new.holders_of(good), old.holders_of(good))
                self.assertEqual(new.goods_flow(good), old.goods_flow(good))
            self.assertEqual(new.goods_totals(), old.goods_totals())
            self.assertEqual(new.edge_agents(), old.edge_agents())
            self.assertEqual(new.edge_goods_agents(), old.edge_goods_agents())
            for edge in ("edge:mint", "edge:world"):
                for currency in CURRENCIES:
                    self.assertEqual(new.edge_volume(edge, currency), old.edge_volume(edge, currency))
                    self.assertEqual(new.edge_net(edge, currency), old.edge_net(edge, currency))
                for good in GOODS:
                    self.assertEqual(new.edge_goods_volume(edge, good), old.edge_goods_volume(edge, good))
                    self.assertEqual(new.edge_goods_net(edge, good), old.edge_goods_net(edge, good))
            self.assertEqual(new.check_conservation(1e-9), old.check_conservation(1e-9))

    def test_post_settled_gives_the_same_record_or_the_same_refusal(self):
        rng = random.Random(5)
        refused = 0
        for _ in range(300):
            new, old = pair_of_books(rng)
            arguments = settled_arguments(rng)
            outcomes = []
            for book in (new, old):
                try:
                    book.post_settled(**arguments)
                    outcomes.append(None)
                except BookError as error:
                    outcomes.append((type(error), str(error)))
            self.assertEqual(outcomes[0], outcomes[1])
            refused += outcomes[0] is not None
            self.assertEqual(new.to_record(), old.to_record())
        self.assertTrue(0 < refused < 300)

    def test_post_settled_with_many_entries_uses_the_array_path_and_agrees(self):
        rng = random.Random(6)
        names = ["h%d" % number for number in range(60)] + ["edge:world"]
        refused = 0
        for round_number in range(60):
            reach = 34.0 if round_number % 2 else 20.0
            new, old = pair_of_books(rng)
            for book in (new, old):
                for name in names[:60]:
                    book.transfer(Transfer("edge:world", name, "coin", 30.0, "start"))
                    book.move(GoodsMove("edge:world", name, "grain", "t1", 6.0, "start"))
            keys = [(name, "t1") for name in names]
            arguments = dict(currency="coin", purpose="sale", item="grain", agents=list(names), keys=keys,
                             paid=[rng.choice([0.0, rng.uniform(0.0, reach)]) for _ in names],
                             received=[rng.choice([0.0, rng.uniform(0.0, reach)]) for _ in names],
                             given=[rng.choice([0.0, rng.uniform(0.0, reach / 5.0)]) for _ in names],
                             taken=[rng.choice([0.0, rng.uniform(0.0, reach / 5.0)]) for _ in names])
            outcomes = []
            for book in (new, old):
                try:
                    book.post_settled(**arguments)
                    outcomes.append(None)
                except BookError as error:
                    outcomes.append((type(error), str(error)))
            self.assertEqual(outcomes[0], outcomes[1])
            refused += outcomes[0] is not None
            self.assertEqual(new.to_record(), old.to_record())
        self.assertTrue(0 < refused < 60, refused)

    def test_start_year_keeps_holdings_and_clears_the_flows(self):
        new, old = pair_of_books(random.Random(8))
        new.start_year()
        old.start_year()
        self.assertEqual(new.to_record(), old.to_record())

    def test_rename_agent_adds_to_what_the_new_name_holds(self):
        rng = random.Random(9)
        for _ in range(60):
            new, old = pair_of_books(rng)
            new.rename_agent("a2", "a3")
            old.rename_agent("a2", "a3")
            self.assertEqual(new.to_record(), old.to_record())
            self.assertFalse(new.knows("a2"))
            self.assertEqual(new.goods_totals(), old.goods_totals())
            self.assertEqual(new.agents(), old.agents())

    def test_absorb_adds_the_other_book(self):
        rng = random.Random(10)
        for _ in range(40):
            new, old = pair_of_books(rng)
            other_new, other_old = pair_of_books(rng)
            new.absorb(other_new)
            old.absorb(other_old)
            self.assertEqual(new.to_record(), old.to_record())

    def test_the_record_filters_by_currency_like_the_reference(self):
        new, old = pair_of_books(random.Random(12))
        self.assertEqual(new.to_record(only=("coin",)), old.to_record(only=("coin",)))
        self.assertEqual(new.to_record(skip=("coin",)), old.to_record(skip=("coin",)))

    def test_from_record_round_trips(self):
        new, _old = pair_of_books(random.Random(14))
        record = new.to_record()
        again = Book.from_record(record)
        self.assertEqual(again.to_record(), record)
        self.assertEqual(again.goods_totals(), new.goods_totals())
        self.assertEqual(again.money_supply("coin"), new.money_supply("coin"))


class BatchReadsAgreeWithSingleReads(unittest.TestCase):
    def test_balances_of_reads_each_agents_balance(self):
        new, _old = pair_of_books(random.Random(21))
        agents = AGENTS + ["nobody"]
        for currency in CURRENCIES + ["unseen"]:
            self.assertEqual(new.balances_of(agents, currency).tolist(), [new.balance(agent, currency) for agent in agents])

    def test_stocks_of_reads_each_agent_and_tile(self):
        new, _old = pair_of_books(random.Random(22))
        agents = AGENTS + ["nobody"] * 3
        tiles = TILES * 3
        self.assertEqual(new.stocks_of("iron", agents, tiles).tolist(),
                         [new.stock(agent, "iron", tile) for agent, tile in zip(agents, tiles)])

    def test_a_read_of_nothing_is_empty(self):
        book = Book()
        self.assertEqual(len(book.stocks_of("iron", [], [])), 0)
        self.assertEqual(book.balances_of(["a"], "coin").tolist(), [0.0])
        self.assertEqual(book.goods_totals(), {})
        self.assertEqual(book.stocks_at(numpy.array([-1], dtype=numpy.int64)).tolist(), [0.0])


if __name__ == "__main__":
    unittest.main()

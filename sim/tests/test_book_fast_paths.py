"""The book's cheap paths (single postings, batch number lookups, one agent's holdings) against the plain code they replace:
the same book record, numbering included, the same errors, the same answers. Plain books, no game."""
QUICK_TOPIC = True

import copy
import random
import unittest

import numpy

from sim.book import Book, BookError, DeliveredMove, GoodsMove, Transfer
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.compiled_tables.ids import IdTable
from sim.tests.book_plain_post import plain_move, plain_post, plain_transfer

AGENTS = ["amy", "bob", "cy", "dee", "edge:mint", "edge:production", "edge:consumption", "producer:flour@rome", "zed"]
CURRENCIES = ["coin", "denarius"]
GOODS = ["grain", "iron", "wine"]
TILES = ["t1", "t2", "t3"]
PURPOSES = ["rent", "sale of grain", "wages for baking", "tax:poll", "state granary", "dividend"]


def random_transfer(rng):
    payer, payee = rng.sample(AGENTS, 2)
    amount = rng.choice([0.0, 0.0, 1.5, rng.uniform(0.0, 40.0), rng.uniform(0.0, 4000.0), -1.0])
    return Transfer(payer, payee, rng.choice(CURRENCIES), amount, rng.choice(PURPOSES))


def random_move(rng):
    giver, receiver = rng.sample(AGENTS, 2)
    quantity = rng.choice([0.0, 2.5, rng.uniform(0.0, 30.0), rng.uniform(0.0, 3000.0), -2.0])
    arguments = (giver, receiver, rng.choice(GOODS), rng.choice(TILES), quantity, rng.choice(PURPOSES))
    if rng.random() < 0.3:
        return DeliveredMove(*arguments, receiver_tile=rng.choice(TILES))
    return GoodsMove(*arguments)


def funded_pair(rng):
    """Two identical books holding money and goods for most agents (seeded through the plain path)."""
    book = Book()
    for agent in AGENTS[:4] + AGENTS[7:]:
        plain_transfer(book, Transfer("edge:mint", agent, "coin", rng.uniform(50.0, 500.0), "start"))
        plain_move(book, GoodsMove("edge:production", agent, rng.choice(GOODS), rng.choice(TILES), rng.uniform(5.0, 80.0), "start"))
    return book, copy.deepcopy(book)


def outcome(action):
    """None when the posting went through, else the error's class and text."""
    try:
        action()
    except BookError as error:
        return type(error), str(error)
    return None


class PostingMethodsAreThePlainPath(unittest.TestCase):
    def run_sequence(self, seed, steps):
        rng = random.Random(seed)
        book, plain = funded_pair(rng)
        for _ in range(steps):
            kind = rng.choice(["transfer", "move", "post", "transfer_many", "move_many", "post_money_only"])
            transfers = [random_transfer(rng) for _ in range(rng.randint(0, 5))]
            moves = [random_move(rng) for _ in range(rng.randint(0, 5))]
            if kind == "transfer":
                single = random_transfer(rng)
                got = outcome(lambda: book.transfer(single))
                want = outcome(lambda: plain_transfer(plain, single))
            elif kind == "move":
                single = random_move(rng)
                got = outcome(lambda: book.move(single))
                want = outcome(lambda: plain_move(plain, single))
            elif kind == "transfer_many":
                got = outcome(lambda: book.transfer_many(transfers))
                want = outcome(lambda: plain_post(plain, transfers, ()))
            elif kind == "move_many":
                got = outcome(lambda: book.move_many(moves))
                want = outcome(lambda: plain_post(plain, (), moves) if moves else None)
            elif kind == "post_money_only":
                got = outcome(lambda: book.post(iter(transfers), ()))
                want = outcome(lambda: plain_post(plain, transfers, ()))
            else:
                got = outcome(lambda: book.post(transfers, moves))
                want = outcome(lambda: plain_post(plain, transfers, moves))
            self.assertEqual(got, want, (seed, kind))
            self.assertEqual(book.to_record(), plain.to_record(), (seed, kind))

    def test_random_postings_leave_the_same_book_and_raise_the_same_errors(self):
        for seed in range(25):
            self.run_sequence(seed, 40)

    def test_a_single_posting_between_new_names_numbers_them_payer_first(self):
        book, plain = Book(), Book()
        book.transfer(Transfer("edge:mint", "newcomer", "silver", 5.0, "seed"))
        plain_transfer(plain, Transfer("edge:mint", "newcomer", "silver", 5.0, "seed"))
        book.transfer(Transfer("newcomer", "another", "silver", 2.0, "sale of wheat"))
        plain_transfer(plain, Transfer("newcomer", "another", "silver", 2.0, "sale of wheat"))
        self.assertEqual(book.numbering_state(), plain.numbering_state())

    def test_a_refused_single_posting_leaves_the_numbering_the_plain_path_leaves(self):
        book, plain = Book(), Book()
        poor = Transfer("pauper", "rich", "coin", 9.0, "rent")
        self.assertEqual(outcome(lambda: book.transfer(poor)), outcome(lambda: plain_transfer(plain, poor)))
        self.assertEqual(book.numbering_state(), plain.numbering_state())


class NumberLookups(unittest.TestCase):
    def test_numbers_of_answers_minus_one_for_a_name_the_table_lacks(self):
        ids = IdTable("agent", ["bob", "amy"])
        self.assertEqual(ids.numbers_of(["bob", "ghost", "amy", "amy"]).tolist(), [1, -1, 0, 0])

    def test_numbers_of_an_empty_list_is_an_empty_integer_array(self):
        found = IdTable("agent", ["bob"]).numbers_of([])
        self.assertEqual((found.tolist(), found.dtype), ([], numpy.dtype(numpy.int64)))

    def test_rows_of_reads_minus_one_for_an_unknown_or_never_posted_agent(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "amy", "coin", 5.0, "seed"))
        book.agent_number("never_posted")
        self.assertEqual(book.rows_of(["amy", "never_posted", "ghost"]).tolist(), [book.agent_number("amy"), -1, -1])

    def test_slots_of_matches_the_slot_of_each_cell(self):
        book, _plain = funded_pair(random.Random(3))
        agents = AGENTS + ["ghost"]
        tiles = (TILES * 4)[:len(agents)]
        for good in GOODS + ["ghost"]:
            self.assertEqual(book.slots_of(good, agents, tiles).tolist(),
                             [book.slot_for(agent, good, tile) for agent, tile in zip(agents, tiles)])


class WholeTableReads(unittest.TestCase):
    def churned_book(self, seed):
        rng = random.Random(seed)
        book, _plain = funded_pair(rng)
        for _ in range(80):
            outcome(lambda: book.move(random_move(rng)))
            outcome(lambda: book.transfer(random_transfer(rng)))
        return book

    def test_balances_by_currency_is_one_balances_at_per_currency(self):
        book = self.churned_book(5)
        rng = random.Random(6)
        names = CURRENCIES + ["unseen"]
        agents = AGENTS + ["ghost"]
        rows = book.rows_of([rng.choice(agents) for _ in range(60)])
        index = numpy.array([rng.randrange(len(names)) for _ in range(60)], dtype=numpy.int64)
        wanted = numpy.zeros(60)
        for each, name in enumerate(names):
            chosen = numpy.nonzero(index == each)[0]
            wanted[chosen] = book.balances_at(rows[chosen], name)
        self.assertEqual(book.balances_by_currency(rows, index, names).tolist(), wanted.tolist())

    def test_balances_by_currency_of_nothing_is_empty(self):
        book = Book()
        self.assertEqual(book.balances_by_currency([], [], []).tolist(), [])

    def test_edge_goods_net_by_good_is_edge_goods_net_of_each_good(self):
        book = self.churned_book(8)
        for edge in [agent for agent in AGENTS if agent.startswith("edge:")] + ["edge:unknown"]:
            nets = book.edge_goods_net_by_good(edge)
            self.assertEqual({good: nets.get(good, 0.0) for good in GOODS}, {good: book.edge_goods_net(edge, good) for good in GOODS})

    def test_goods_flows_is_goods_flow_of_each_good(self):
        book = self.churned_book(9)
        flows = book.goods_flows()
        for good in GOODS + ["unseen"]:
            self.assertEqual(list(flows.get(good, {}).items()), list(book.goods_flow(good).items()), good)


class AgentNumbersInOrder(unittest.TestCase):
    def test_new_names_are_numbered_as_one_by_one_admission_numbers_them(self):
        names = ["zed", "amy", "known", "zed", "bob", "amy"]
        batch, single = Book(), Book()
        batch.agent_number("known")
        single.agent_number("known")
        self.assertEqual((batch.agent_numbers_in_order(names), batch.numbering_state()),
                         ([single.agent_number(name) for name in names], single.numbering_state()))

    def test_no_names_admit_nothing(self):
        book = Book()
        self.assertEqual((book.agent_numbers_in_order([]), len(book.agent_ids)), ([], 0))


def plain_goods_of(book, agent):
    """The held-goods dict as `Book.goods_of` has always built it."""
    number = book.agent_ids.numbers.get(agent)
    held = {}
    if number is None:
        return held
    slot = book.agent_table.first_slot.item(number)
    table = book.stock_rows.table
    while slot != -1:
        good, tile = book.good_ids.name(table.good.item(slot)), book.tile_ids.name(table.tile.item(slot))
        held.setdefault(good, {})[tile] = table.quantity.item(slot)
        slot = table.next_in_agent.item(slot)
    return held


def plain_goods_held(book, agent):
    goods = {}
    for good, by_tile in sorted(plain_goods_of(book, agent).items()):
        tiles = {tile: value for tile, value in sorted(by_tile.items()) if value != 0.0}
        if tiles:
            goods[good] = tiles
    return goods


class HoldingsReads(unittest.TestCase):
    def test_goods_held_and_holdings_match_the_slot_chain_read_one_by_one(self):
        rng = random.Random(11)
        book, _plain = funded_pair(rng)
        for _ in range(60):
            outcome(lambda: book.move(random_move(rng)))
            outcome(lambda: book.transfer(random_transfer(rng)))
        for agent in AGENTS + ["ghost"]:
            self.assertEqual(book.goods_held(agent), plain_goods_held(book, agent), agent)
            self.assertEqual(book.goods_of(agent), plain_goods_of(book, agent), agent)
            self.assertEqual(book.holdings(agent)["goods"], plain_goods_held(book, agent), agent)

    def test_holdings_money_lists_nonzero_seen_currencies_in_name_order(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "amy", "silver", 3.0, "seed"))
        book.transfer(Transfer("edge:mint", "amy", "coin", 4.0, "seed"))
        book.transfer(Transfer("amy", "bob", "coin", 4.0, "seed"))
        holdings = book.holdings("amy")
        self.assertEqual((list(holdings["money"].items()), holdings["goods"]), ([("silver", 3.0)], {}))


def old_apply_batches(book, transfers, moves, batch_count, rule=0):
    """`apply_batches` as it was when every batch ran both halves, written over the same kernel pieces: the outcome of each batch."""
    from sim.book_apply import plan_goods_batch, plan_money_batch
    from sim.book_commit import commit_money, commit_stock, record_moves, record_transfers
    from sim.book_post import grown_scratch
    from sim.compiled_tables.causes import OK
    from sim.compiled_tables.grouping import group_starts
    book._reserve_for_moves(int(moves.row_count[0]))
    transfer_starts = group_starts(transfers.batch, int(transfers.row_count[0]), batch_count)
    move_starts = group_starts(moves.batch, int(moves.row_count[0]), batch_count)
    book.scratch = scratch = grown_scratch(book.scratch, int(numpy.diff(transfer_starts).max()), int(numpy.diff(move_starts).max()))
    tables = book.tables()
    outcomes = []
    for batch in range(batch_count):
        transfer_first, transfer_last = int(transfer_starts[batch]), int(transfer_starts[batch + 1])
        move_first, move_last = int(move_starts[batch]), int(move_starts[batch + 1])
        code, culprit = plan_money_batch(transfers, transfer_first, transfer_last, tables.money, scratch.money_plan,
                                         scratch.money_local, rule)
        if code == OK:
            code, culprit = plan_goods_batch(moves, move_first, move_last, tables.goods, scratch.goods_plan,
                                             scratch.goods_local, rule)
        if code == OK:
            commit_money(scratch.money_plan, tables.money.balances, tables.money.agents)
            code = commit_stock(scratch.goods_plan, tables.goods.stocks, tables.goods.stock_index, tables.goods.agents)
            culprit = -1
            if code == OK:
                record_transfers(transfers, transfer_first, transfer_last, tables.money)
                code = record_moves(moves, move_first, move_last, tables.goods)
        outcomes.append((int(code), int(culprit)))
    return outcomes


def posting_tables(book, transfers, moves):
    """The two posting tables of (batch, posting) pairs, every name admitted to the book."""
    transfer_rows = [(book.agent_number(each.payer), book.agent_number(each.payee), book.currency_number(each.currency), each.amount,
                      *book.purposes.encode(each.purpose), batch) for batch, each in transfers]
    move_rows = [(book.agent_number(each.giver), book.agent_number(each.receiver), book.good_number(each.good),
                  book.tile_number(each.tile), book.tile_number(getattr(each, "receiver_tile", "") or each.tile), each.quantity,
                  *book.purposes.encode(each.purpose), batch) for batch, each in moves]
    result = []
    for spec, table_type, rows in ((TRANSFER_POSTINGS, TransferPostings, transfer_rows),
                                   (GOODS_MOVE_POSTINGS, GoodsMovePostings, move_rows)):
        columns = list(map(list, zip(*rows))) if rows else [[] for _column in spec.columns]
        result.append(spec.table_of(table_type, **dict(zip([column.name for column in spec.columns], columns))))
    return result


class BatchesSkipTheEmptyHalf(unittest.TestCase):
    def test_mixed_batches_leave_the_book_the_two_half_kernel_left_it(self):
        for seed in range(20):
            rng = random.Random(seed)
            book, plain = funded_pair(rng)
            batch_count = rng.randint(1, 14)
            transfers, moves = [], []
            for batch in range(batch_count):
                shape = rng.choice(["money", "goods", "both", "empty"])
                for _ in range(rng.randint(1, 4) if shape in ("money", "both") else 0):
                    transfers.append((batch, random_transfer(rng)))
                for _ in range(rng.randint(1, 4) if shape in ("goods", "both") else 0):
                    moves.append((batch, random_move(rng)))
            transfers = [(batch, each) for batch, each in transfers if each.amount >= 0.0]
            moves = [(batch, each) for batch, each in moves if each.quantity >= 0.0]
            new_transfers, new_moves = posting_tables(book, transfers, moves)
            old_transfers, old_moves = posting_tables(plain, transfers, moves)
            outcomes, _scratch = book.apply_postings(new_transfers, new_moves, batch_count)
            wanted = old_apply_batches(plain, old_transfers, old_moves, batch_count)
            self.assertEqual(list(zip(outcomes.code[:batch_count].tolist(), outcomes.culprit[:batch_count].tolist())), wanted, seed)
            self.assertEqual(book.to_record(), plain.to_record(), seed)


if __name__ == "__main__":
    unittest.main()

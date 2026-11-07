"""Several markets' pairs of one item settled in one kernel call and posted on the book once.

The markets are settled in the order given, as if one after another: a purse or a stock one market spent is not there for
the next (`settlement_batch_kernel.settle_markets`). Each market gets its own `Settlement`, so the year ledger notes it as
before; the book is posted with the batch's sums per agent and per (agent, tile) key (`Book.post_settled`).

The (agent, tile) keys and the agents are numbered once for the whole batch (`KeyTable`, in order of first use); each market's
own keys and agents are those its pairs use, found by one sort over the batch (`settle_packed`). `settle_many` packs
`Pairing`s; settlement_arrays.py packs the clearings that hold arrays.
"""
from functools import lru_cache
from typing import Callable, Dict, FrozenSet, List, Optional, Sequence, Tuple

import numpy

from sim.book import Book
from .settlement_batch_kernel import settle_markets
from .settlement_record import Settlement
from .types import EDGE_MINT, AgentId, CurrencyId, Pairing, is_edge, is_external_edge


@lru_cache(maxsize=None)
def _kind(agent: AgentId) -> Tuple[bool, bool, bool]:
    """(is an edge account, is the mint, is a foreign edge account) of an agent id."""
    return is_edge(agent), agent == EDGE_MINT, is_external_edge(agent)


class KeyTable:
    """The (agent, tile) keys and the agents of one batch, numbered in order of first use."""

    def __init__(self):
        self.keys: List[Tuple[AgentId, str]] = []
        self.number: Dict[Tuple[AgentId, str], int] = {}
        self.agents: List[AgentId] = []
        self.agent_number: Dict[AgentId, int] = {}
        self.key_agent: List[int] = []

    def key(self, agent: AgentId, tile: str) -> int:
        found = self.number.get((agent, tile))
        if found is None:
            found = self.number[(agent, tile)] = len(self.keys)
            self.keys.append((agent, tile))
            number = self.agent_number.get(agent)
            if number is None:
                number = self.agent_number[agent] = len(self.agents)
                self.agents.append(agent)
            self.key_agent.append(number)
        return found


class Packed:
    """A batch's pairs, market after market: `sizes` pairs per market, then per pair the receiving key, the selling key, the
    quantity and the seller's ask; `sources[market]` gives the `Pairing` of a market (None where it has no pairs)."""

    def __init__(self):
        self.sizes: List[int] = []
        self.receipt: List[numpy.ndarray] = []
        self.seller: List[numpy.ndarray] = []
        self.quantity: List[numpy.ndarray] = []
        self.ask: List[numpy.ndarray] = []
        self.sources: List[Optional[Callable[[], Pairing]]] = []


def pack_pairings(table: KeyTable, pairings: Sequence[Pairing], delivers_goods: bool) -> Packed:
    packed = Packed()
    for pairing in pairings:
        count = len(pairing.quantity)
        packed.sizes.append(count)
        if not count:
            packed.sources.append(None)
            continue
        buyers, sellers = pairing.buyers, pairing.sellers
        buyer_index = numpy.array(pairing.buyer_index, dtype=numpy.int64)
        seller_index = numpy.array(pairing.seller_index, dtype=numpy.int64)
        bid_key = numpy.zeros(len(buyers), dtype=numpy.int64)
        used_bids = numpy.unique(buyer_index).tolist()
        for index in used_bids:
            bid_key[index] = table.key(*buyers[index])
        offer_key = numpy.zeros(len(sellers), dtype=numpy.int64)
        for index in numpy.unique(seller_index).tolist():
            offer_key[index] = table.key(*sellers[index])
        receipt = bid_key[buyer_index]
        if delivers_goods and not all(buyers[index][1] for index in used_bids):
            # a buyer with no tile takes delivery where the seller holds the goods
            buyer_list, seller_list = pairing.buyer_index, pairing.seller_index
            receipt = numpy.array([receipt[pair] if buyers[buyer_list[pair]][1] else
                                   table.key(buyers[buyer_list[pair]][0], sellers[seller_list[pair]][1])
                                   for pair in range(count)], dtype=numpy.int64)
        packed.receipt.append(receipt)
        packed.seller.append(offer_key[seller_index])
        packed.quantity.append(numpy.array(pairing.quantity, dtype=float))
        packed.ask.append(numpy.array(pairing.asks, dtype=float)[seller_index])
        packed.sources.append(lambda held=pairing: held)
    return packed


def settle_many(book: Book, pairings: Sequence[Pairing], currency: CurrencyId, item: str, purpose: str,
                delivers_goods: bool, import_accounts: FrozenSet[AgentId], export_accounts: FrozenSet[AgentId]
                ) -> List[Settlement]:
    """One `Settlement` per pairing, each market settled on what the earlier ones left, the book posted once. A pairing with
    no pairs settles nothing. Each seller is limited to the stock it holds of `item` on its tile and each payer to its money."""
    table = KeyTable()
    packed = pack_pairings(table, pairings, delivers_goods)
    return settle_packed(book, table, packed, currency, item, purpose, delivers_goods, import_accounts, export_accounts)


def settle_packed(book: Book, table: KeyTable, packed: Packed, currency: CurrencyId, item: str, purpose: str,
                  delivers_goods: bool, import_accounts: FrozenSet[AgentId], export_accounts: FrozenSet[AgentId]
                  ) -> List[Settlement]:
    """`settle_many` of pairs already packed against `table`."""
    markets = len(packed.sizes)
    settlements = [Settlement(item=item, purpose=purpose, currency=currency) for _ in range(markets)]
    if not table.agents:
        return settlements
    sizes = numpy.array(packed.sizes, dtype=numpy.int64)
    pair_offset = numpy.concatenate(([0], numpy.cumsum(sizes))).astype(numpy.int64)
    pair_count = int(pair_offset[-1])
    receipt, seller = numpy.concatenate(packed.receipt), numpy.concatenate(packed.seller)
    market_of_pair = numpy.repeat(numpy.arange(markets, dtype=numpy.int64), sizes)
    key_total, agent_total = len(table.keys), len(table.agents)
    unique, inverse = numpy.unique(numpy.concatenate((market_of_pair * key_total + receipt, market_of_pair * key_total + seller)),
                                   return_inverse=True)
    key_market, key_global = unique // key_total, unique % key_total
    market_ids = numpy.arange(markets + 1, dtype=numpy.int64)
    key_offset = numpy.searchsorted(key_market, market_ids).astype(numpy.int64)
    shift = key_offset[market_of_pair]
    inverse = inverse.reshape(-1)
    buyer_key, seller_key = inverse[:pair_count] - shift, inverse[pair_count:] - shift
    unique_agents, agent_inverse = numpy.unique(
        key_market * agent_total + numpy.array(table.key_agent, dtype=numpy.int64)[key_global], return_inverse=True)
    agent_market, agent_global = unique_agents // agent_total, unique_agents % agent_total
    agent_offset = numpy.searchsorted(agent_market, market_ids).astype(numpy.int64)
    key_agent = agent_inverse.reshape(-1) - agent_offset[key_market]
    agents, keys = table.agents, table.keys
    stock_state = numpy.zeros(key_total)
    if delivers_goods:
        for number in numpy.unique(seller).tolist():
            agent, tile = keys[number]
            stock_state[number] = book.stock(agent, item, tile)
    cash_state = numpy.array([book.balance(agent, currency) for agent in agents])
    kinds = [_kind(agent) for agent in agents]
    (goods, money, payer, paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports, exports,
     _key_given, _key_taken, key_to_mint, batch_paid, batch_received, batch_given, batch_taken) = settle_markets(
        pair_offset, agent_offset, key_offset, buyer_key, seller_key, numpy.concatenate(packed.quantity),
        numpy.concatenate(packed.ask), key_agent, key_global, agent_global, stock_state, cash_state,
        numpy.array([kind[0] for kind in kinds], dtype=numpy.bool_), numpy.array([kind[1] for kind in kinds], dtype=numpy.bool_),
        numpy.array([kind[2] for kind in kinds], dtype=numpy.bool_),
        numpy.array([agent in import_accounts for agent in agents], dtype=numpy.bool_),
        numpy.array([agent in export_accounts for agent in agents], dtype=numpy.bool_), delivers_goods, delivers_goods)
    book.post_settled(currency, purpose, item, agents, batch_paid.tolist(), batch_received.tolist(), keys,
                      batch_given.tolist(), batch_taken.tolist())
    columns = [each.tolist() for each in (paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports,
                                          exports)]
    agent_ids, key_ids, mint_column = agent_global.tolist(), key_global.tolist(), key_to_mint.tolist()
    pair_cuts, agent_cuts, key_cuts = pair_offset.tolist(), agent_offset.tolist(), key_offset.tolist()
    for market, settlement in enumerate(settlements):
        first_pair, last_pair = pair_cuts[market], pair_cuts[market + 1]
        if last_pair == first_pair:
            continue
        first, last = agent_cuts[market], agent_cuts[market + 1]
        first_key, last_key = key_cuts[market], key_cuts[market + 1]
        settlement.agents = [agents[number] for number in agent_ids[first:last]]
        settlement.keys = [keys[number] for number in key_ids[first_key:last_key]]
        (settlement.paid, settlement.received, settlement.goods_in, settlement.goods_out, settlement.buyer_net,
         settlement.got_goods, settlement.paid_as_buyer, settlement.imports, settlement.exports) = (
            column[first:last] for column in columns)
        settlement.key_to_mint = mint_column[first_key:last_key]
        settlement.delivered = float(goods[first_pair:last_pair].sum())
        settlement.pairs = (packed.sources[market], buyer_key[first_pair:last_pair], payer[first_pair:last_pair],
                            goods[first_pair:last_pair], money[first_pair:last_pair])
    return settlements

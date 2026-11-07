"""Several markets' pairings of one item settled in one kernel call and posted on the book once.

The markets are settled in the order given, as if one after another: a purse or a stock one market spent is not there for
the next (`settlement_batch_kernel.settle_markets`). Each market gets its own `Settlement`, so the year ledger notes it as
before; the book is posted with the batch's sums per agent and per (agent, tile) key (`Book.post_settled`).
"""
from functools import lru_cache
from typing import Dict, FrozenSet, List, Sequence, Tuple

import numpy

from sim.book import Book
from .settlement_batch_kernel import settle_markets
from .settlement_record import Settlement
from .types import EDGE_MINT, AgentId, CurrencyId, Pairing, is_edge, is_external_edge


@lru_cache(maxsize=None)
def _kind(agent: AgentId) -> Tuple[bool, bool, bool]:
    """(is an edge account, is the mint, is a foreign edge account) of an agent id."""
    return is_edge(agent), agent == EDGE_MINT, is_external_edge(agent)


def _numbered(table, names: Sequence[Tuple[AgentId, str]], used: List[int]) -> numpy.ndarray:
    """For each index of `used` (ascending) into `names`, the table's number of that (agent, tile) key; others are left at zero."""
    numbers = numpy.zeros(len(names), dtype=numpy.int64)
    keys, number_of, agents, agent_number = table.keys, table.number, table.agents, table.agent_number
    for index in used:
        key = names[index]
        number = number_of.get(key)
        if number is None:
            number = number_of[key] = len(keys)
            keys.append(key)
            if key[0] not in agent_number:
                agent_number[key[0]] = len(agents)
                agents.append(key[0])
        numbers[index] = number
    return numbers


class _Keys:
    """The (agent, tile) keys and the agents of one market, numbered in order of first use."""

    def __init__(self):
        self.keys: List[Tuple[AgentId, str]] = []
        self.number: Dict[Tuple[AgentId, str], int] = {}
        self.agents: List[AgentId] = []
        self.agent_number: Dict[AgentId, int] = {}

    def add(self, key: Tuple[AgentId, str]) -> int:
        number = self.number.get(key)
        if number is None:
            number = self.number[key] = len(self.keys)
            self.keys.append(key)
            if key[0] not in self.agent_number:
                self.agent_number[key[0]] = len(self.agents)
                self.agents.append(key[0])
        return number


def settle_many(book: Book, pairings: Sequence[Pairing], currency: CurrencyId, item: str, purpose: str,
                delivers_goods: bool, import_accounts: FrozenSet[AgentId], export_accounts: FrozenSet[AgentId]
                ) -> List[Settlement]:
    """One `Settlement` per pairing, each market settled on what the earlier ones left, the book posted once. A pairing with
    no pairs settles nothing. Each seller is limited to the stock it holds of `item` on its tile and each payer to its money."""
    settlements = [Settlement(item=item, purpose=purpose, currency=currency) for _ in pairings]
    batch_agents: Dict[AgentId, int] = {}
    batch_keys: Dict[Tuple[AgentId, str], int] = {}
    pair_offset, agent_offset, key_offset = [0], [0], [0]
    buyer_key: List[numpy.ndarray] = []
    seller_key: List[numpy.ndarray] = []
    quantity: List[object] = []
    ask: List[numpy.ndarray] = []
    key_agent: List[int] = []
    key_global: List[int] = []
    agent_global: List[int] = []
    seller_keys = set()
    receipts: List[object] = []
    tables: List[_Keys] = []
    for pairing in pairings:
        count = len(pairing.quantity)
        if not count:
            pair_offset.append(pair_offset[-1])
            agent_offset.append(agent_offset[-1])
            key_offset.append(key_offset[-1])
            receipts.append(None)
            tables.append(None)
            continue
        table = _Keys()
        buyers, sellers = pairing.buyers, pairing.sellers
        buyer_index = numpy.array(pairing.buyer_index, dtype=numpy.int64)
        seller_index = numpy.array(pairing.seller_index, dtype=numpy.int64)
        used_bids = numpy.unique(buyer_index).tolist()
        used_offers = numpy.unique(seller_index).tolist()
        bid_key = _numbered(table, buyers, used_bids)
        offer_key = _numbered(table, sellers, used_offers)
        buyers_here = bid_key[buyer_index]
        sellers_here = offer_key[seller_index]
        receipt = buyers_here
        if delivers_goods and not all(buyers[index][1] for index in used_bids):
            # a buyer with no tile takes delivery where the seller holds the goods
            buyer_list, seller_list, here = pairing.buyer_index, pairing.seller_index, buyers_here.tolist()
            receipt = numpy.array([here[pair] if buyers[buyer_list[pair]][1] else
                                   table.add((buyers[buyer_list[pair]][0], sellers[seller_list[pair]][1]))
                                   for pair in range(count)], dtype=numpy.int64)
        buyer_key.append(receipt)
        seller_key.append(sellers_here)
        quantity.append(pairing.quantity)
        ask.append(numpy.array(pairing.asks, dtype=float)[seller_index])
        agent_numbers = table.agent_number
        key_agent.extend([agent_numbers[agent] for agent, _tile in table.keys])
        agent_global.extend([batch_agents.setdefault(agent, len(batch_agents)) for agent in table.agents])
        global_keys = [batch_keys.setdefault(key, len(batch_keys)) for key in table.keys]
        key_global.extend(global_keys)
        if delivers_goods:
            seller_keys.update([global_keys[number] for number in numpy.unique(sellers_here).tolist()])
        pair_offset.append(pair_offset[-1] + count)
        agent_offset.append(agent_offset[-1] + len(table.agents))
        key_offset.append(key_offset[-1] + len(table.keys))
        receipts.append(receipt)
        tables.append(table)
    if not batch_agents:
        return settlements
    agents, keys = list(batch_agents), list(batch_keys)
    kinds = [_kind(agent) for agent in agents]
    stock_state = numpy.zeros(len(keys))
    for number in seller_keys:
        agent, tile = keys[number]
        stock_state[number] = book.stock(agent, item, tile)
    cash_state = numpy.array([book.balance(agent, currency) for agent in agents])
    (goods, money, payer, paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports, exports,
     key_given, key_taken, key_to_mint, batch_paid, batch_received, batch_given, batch_taken) = settle_markets(
        numpy.array(pair_offset, dtype=numpy.int64), numpy.array(agent_offset, dtype=numpy.int64),
        numpy.array(key_offset, dtype=numpy.int64), numpy.concatenate(buyer_key),
        numpy.concatenate(seller_key), numpy.concatenate([numpy.array(each, dtype=float) for each in quantity]),
        numpy.concatenate(ask),
        numpy.array(key_agent, dtype=numpy.int64), numpy.array(key_global, dtype=numpy.int64),
        numpy.array(agent_global, dtype=numpy.int64), stock_state, cash_state,
        numpy.array([kind[0] for kind in kinds], dtype=numpy.bool_), numpy.array([kind[1] for kind in kinds], dtype=numpy.bool_),
        numpy.array([kind[2] for kind in kinds], dtype=numpy.bool_),
        numpy.array([agent in import_accounts for agent in agents], dtype=numpy.bool_),
        numpy.array([agent in export_accounts for agent in agents], dtype=numpy.bool_), delivers_goods, delivers_goods)
    book.post_settled(currency, purpose, item, agents, batch_paid.tolist(), batch_received.tolist(), keys,
                      batch_given.tolist(), batch_taken.tolist())
    columns = [each.tolist() for each in (paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports,
                                          exports, key_to_mint)]
    for market, (pairing, settlement, table) in enumerate(zip(pairings, settlements, tables)):
        if table is None:
            continue
        first, last = agent_offset[market], agent_offset[market + 1]
        first_key, last_key = key_offset[market], key_offset[market + 1]
        first_pair, last_pair = pair_offset[market], pair_offset[market + 1]
        settlement.agents, settlement.keys = table.agents, table.keys
        (settlement.paid, settlement.received, settlement.goods_in, settlement.goods_out, settlement.buyer_net,
         settlement.got_goods, settlement.paid_as_buyer, settlement.imports, settlement.exports) = (
            column[first:last] for column in columns[:9])
        settlement.key_to_mint = columns[9][first_key:last_key]
        settlement.delivered = float(goods[first_pair:last_pair].sum())
        settlement.pairs = (pairing, receipts[market], payer[first_pair:last_pair], goods[first_pair:last_pair],
                            money[first_pair:last_pair])
    return settlements

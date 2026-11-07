"""What a market's settlement did, summed (`Settlement`), kept for the year ledger and the buyers' maps."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sim.book import DeliveredMove
from .types import AgentId, CurrencyId, Transfer


@dataclass
class Settlement:
    """What a market's settlement did, summed: per agent the money it paid and received and the goods it got and gave, per
    (agent, tile) key the goods delivered to the mint, and per pair the goods and money moved. `imports` and `exports` are
    the year ledger's foreign-money figures by agent (`YearLedger._note_foreign`)."""
    item: str = ""
    purpose: str = ""
    currency: CurrencyId = ""
    agents: List[AgentId] = field(default_factory=list)
    paid: List[float] = field(default_factory=list)
    received: List[float] = field(default_factory=list)
    goods_in: List[float] = field(default_factory=list)
    goods_out: List[float] = field(default_factory=list)
    buyer_net: List[float] = field(default_factory=list)       # money paid as a buyer, net of money paid to take
    got_goods: List[bool] = field(default_factory=list)
    paid_as_buyer: List[bool] = field(default_factory=list)
    imports: List[float] = field(default_factory=list)
    exports: List[float] = field(default_factory=list)
    keys: List[Tuple[AgentId, str]] = field(default_factory=list)
    key_to_mint: List[float] = field(default_factory=list)
    delivered: float = 0.0                                     # goods moved
    pairs: Optional[Tuple] = None      # (pairing, receipt_key, payer, goods, money) for `postings`

    @property
    def postings(self) -> List[object]:
        """The Transfers and GoodsMoves applied, one of each per pair that moved something."""
        if self.pairs is None:
            return []
        pairing, receipt_key, payer, goods, money = self.pairs
        buyer_index, seller_index = pairing.buyer_index, pairing.seller_index
        transfers, moves = [], []
        for pair in range(len(goods)):
            buyer = pairing.buyers[buyer_index[pair]]
            seller = pairing.sellers[seller_index[pair]]
            if goods[pair] > 0.0:
                moves.append(DeliveredMove(seller[0], buyer[0], self.item, seller[1], float(goods[pair]), self.purpose,
                                           self.keys[receipt_key[pair]][1]))
            if money[pair] > 0.0:
                paying = self.agents[payer[pair]]
                transfers.append(Transfer(paying, seller[0] if paying == buyer[0] else buyer[0], self.currency,
                                          float(money[pair]), self.purpose))
        return transfers + moves

    @property
    def buyer_money(self) -> Dict[AgentId, float]:
        return {agent: net for agent, net, seen in zip(self.agents, self.buyer_net, self.paid_as_buyer) if seen}

    @property
    def paid_to(self) -> Dict[AgentId, float]:
        """Agent -> money it received (only those that received any)."""
        return {agent: amount for agent, amount in zip(self.agents, self.received) if amount > 0.0}

    @property
    def paid_by(self) -> Dict[AgentId, float]:
        """Agent -> money it paid (only those that paid any)."""
        return {agent: amount for agent, amount in zip(self.agents, self.paid) if amount > 0.0}

    def bought_by_buyer(self) -> Dict[AgentId, Tuple[float, float]]:
        """Of a goods settlement, buyer -> (units it received, money it paid net of any it was paid to take). Only the buyer
        side of each sale counts: money a buyer receives as a seller in the same market is not netted out."""
        bought: Dict[AgentId, Tuple[float, float]] = {}
        for agent, units, got, net, seen in zip(self.agents, self.goods_in, self.got_goods, self.buyer_net,
                                                self.paid_as_buyer):
            if got or seen:
                bought[agent] = (units, net if seen else 0.0)
        return bought

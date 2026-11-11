"""The title sale market (Complaint 538): holders who would rather have money offer hectares of a title, buyers bid from
what the rent stream is worth to them, and a tile clears at one price.

Plain functions of the actors' own figures; any actor (a household, a firm, a state) can be a seller or a buyer. A hectare is
worth to an actor its rent over the rate it discounts at: its own best alternative (time preference plus the inflation it
expects, the state's bonds where in reach), never the lending rate the market clears at. A holder who needs cash discounts at
the rate cash costs it, so it asks less. The price a tile's hectares changed hands at is what the lenders read as the yield
of land (`lender_ask.land_yield`), which no rate capitalises.
"""
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import lender_ask, titles_value
from .types import AgentId, TileId


@dataclass(frozen=True)
class Seller:
    agent_id: AgentId
    hectares: float                 # hectares offered
    lowest_price: float             # the least it takes a hectare


@dataclass(frozen=True)
class Buyer:
    agent_id: AgentId
    hectares: float                 # hectares wanted at no more than the bid, within its cash
    highest_price: float            # the most it pays a hectare


@dataclass(frozen=True)
class Sale:
    seller: AgentId
    buyer: AgentId
    hectares: float
    price_per_hectare: float


def discount_rate(time_preference: float, expected_inflation: float, public_yield: Optional[float] = None) -> float:
    """The rate an actor discounts a rent stream at: the best return its money earns elsewhere (no land yield, no loss)."""
    return lender_ask.lowest_ask(time_preference, expected_inflation, public_yield=public_yield)


def seller_discount_rate(own_rate: float, cost_of_cash: Optional[float]) -> float:
    """The rate a holder short of cash discounts at: what cash costs it where that is more than its own alternative."""
    return own_rate if cost_of_cash is None else max(own_rate, cost_of_cash)


def asking_offer(agent_id: AgentId, free_hectares: float, rent_per_hectare: float, rate: float,
                 cash_needed: float = 0.0) -> Optional[Seller]:
    """The hectares a holder offers at the least its rent is worth to it at `rate`. One that needs `cash_needed` offers no
    more hectares than raise it at that price; one that needs none offers its whole free title. None when nothing is offered."""
    price = titles_value.hectare_value(rent_per_hectare, rate)
    if price <= 0.0 or free_hectares <= 0.0:
        return None
    hectares = min(free_hectares, cash_needed / price) if cash_needed > 0.0 else free_hectares
    return Seller(agent_id, hectares, price) if hectares > 0.0 else None


def bid_for(agent_id: AgentId, rent_per_hectare: float, rate: float, cash: float) -> Optional[Buyer]:
    """A bid at the rent stream's worth at the buyer's rate, for no more hectares than its cash buys at that price."""
    price = titles_value.hectare_value(rent_per_hectare, rate)
    if price <= 0.0 or cash <= 0.0:
        return None
    return Buyer(agent_id, cash / price, price)


def clear_tile(sellers: Sequence[Seller], buyers: Sequence[Buyer]) -> List[Sale]:
    """Sales at one price: the cheapest sellers meet the dearest buyers while a buyer's bid is above a seller's ask. The price is the
    middle of the dearest ask and the lowest bid among those that traded, so it lies between each side's valuation. Nothing
    trades where the valuations do not cross. The caller keeps sellers and buyers apart (no actor is on both sides)."""
    asks = sorted(((seller.lowest_price, seller.agent_id, seller.hectares) for seller in sellers))
    bids = sorted(((-buyer.highest_price, buyer.agent_id, buyer.hectares) for buyer in buyers))
    matches: List[Tuple[AgentId, AgentId, float]] = []
    dearest_ask = lowest_bid = 0.0
    ask_at, bid_at = 0, 0
    asks_left = [hectares for _price, _agent, hectares in asks]
    bids_left = [hectares for _price, _agent, hectares in bids]
    while ask_at < len(asks) and bid_at < len(bids):
        ask_price, seller, _ = asks[ask_at]
        bid_price, buyer, _ = bids[bid_at]
        if -bid_price <= ask_price:      # equal valuations gain neither side anything
            break
        moved = min(asks_left[ask_at], bids_left[bid_at])
        matches.append((seller, buyer, moved))
        dearest_ask, lowest_bid = ask_price, -bid_price
        asks_left[ask_at] -= moved
        bids_left[bid_at] -= moved
        if asks_left[ask_at] <= 1e-12:
            ask_at += 1
        if bids_left[bid_at] <= 1e-12:
            bid_at += 1
    if not matches:
        return []
    price = (dearest_ask + lowest_bid) / 2.0
    return [Sale(seller, buyer, hectares, price) for seller, buyer, hectares in matches]


def year_price(sales: Sequence[Sale]) -> Optional[float]:
    """The hectare-weighted price of the sales; None where there were none."""
    hectares = sum(sale.hectares for sale in sales)
    return sum(sale.price_per_hectare * sale.hectares for sale in sales) / hectares if hectares > 0.0 else None


def market_land_yield(rent_by_tile: Mapping[TileId, float], price_by_tile: Mapping[TileId, float],
                      hectares_by_tile: Mapping[TileId, float]) -> Optional[float]:
    """What a hectare earns over what the year's sales paid for it: the rent of the tiles that sold over their prices,
    each weighted by the hectares sold. None where nothing sold."""
    sold = [tile for tile in sorted(price_by_tile) if hectares_by_tile.get(tile, 0.0) > 0.0]
    hectares = sum(hectares_by_tile[tile] for tile in sold)
    if hectares <= 0.0:
        return None
    rent = sum(rent_by_tile.get(tile, 0.0) * hectares_by_tile[tile] for tile in sold) / hectares
    price = sum(price_by_tile[tile] * hectares_by_tile[tile] for tile in sold) / hectares
    return lender_ask.land_yield(rent, price)


def proceeds(sales: Sequence[Sale]) -> Dict[AgentId, float]:
    """Money each seller takes."""
    taken: Dict[AgentId, float] = {}
    for sale in sales:
        taken[sale.seller] = taken.get(sale.seller, 0.0) + sale.hectares * sale.price_per_hectare
    return taken

"""Foreign partners as external sellers and buyers, booked against `EDGE_EXTERNAL`.

Partner economies are not agents yet. The engine's port hands over what they would sell and buy:
  * `external_orders` -> `AgentOrders`: offers of imports at the landed price on the port tile
    (the partner's price plus carriage and the cargo's costs, already counted by the caller), and
    bids for our exports at the partner's price less carriage to its market.
  * `balance_of_payments` reads the year's money through `EDGE_EXTERNAL` from the book: what domestic
    buyers paid for imports less what the partner paid for exports. Positive `net_outflow` is money
    leaving the economy.
Settlement is the ordinary goods-market path: the edge account is never short of goods or money.
"""
from dataclasses import dataclass
from typing import Callable, Mapping, Optional

from sim.constants import declare

from .accounts import Book
from .protocols import AgentOrders
from .types import EDGE_EXTERNAL, AreaId, Bid, CurrencyId, GoodId, Offer, TileId

EXTERNAL_BID_ELASTICITY = declare(
    "EXTERNAL_BID_ELASTICITY", 6.0, kind="temporary_heuristic", unit="dimensionless",
    source=None, confidence="D",
    why="A partner's demand for our exports falls steeply as our price rises above what it can get at "
        "home; the schedule form has no hard ceiling, so a steep curve stands in. Partner demand "
        "curves are not yet modelled.")


@dataclass(frozen=True)
class BalanceOfPayments:
    imports_paid: float          # money domestic buyers paid to the partners
    exports_received: float      # money partners paid for our goods
    net_outflow: float           # imports_paid - exports_received


def external_orders(landed_prices: Mapping[GoodId, float], export_prices: Mapping[GoodId, float],
                    quantities_available: Mapping[GoodId, float], quantities_wanted: Mapping[GoodId, float],
                    area_of: Callable[[GoodId, TileId], AreaId], port_tile: TileId,
                    export_carriage_per_unit: Optional[Mapping[GoodId, float]] = None,
                    export_budget: Optional[float] = None) -> AgentOrders:
    """Offers of imports at `landed_prices` (per unit, on `port_tile`) up to `quantities_available`;
    bids for exports at `export_prices` less `export_carriage_per_unit`, up to `quantities_wanted`.
    A good whose net export price is not positive draws no bid. `export_budget`, when given, is what
    the partners can pay this year, shared among the bids by the value each wants."""
    carriage = export_carriage_per_unit or {}
    offers = tuple(Offer(EDGE_EXTERNAL, good, area_of(good, port_tile), port_tile,
                         quantities_available[good], landed_prices[good])
                   for good in sorted(landed_prices)
                   if quantities_available.get(good, 0.0) > 0.0)
    wanted_rows = []
    for good in sorted(export_prices):
        net_price = export_prices[good] - carriage.get(good, 0.0)
        wanted = quantities_wanted.get(good, 0.0)
        if net_price > 0.0 and wanted > 0.0:
            wanted_rows.append((good, net_price, wanted))
    total_value = sum(net_price * wanted for _good, net_price, wanted in wanted_rows)
    bids = []
    for good, net_price, wanted in wanted_rows:
        budget = (float("inf") if export_budget is None or total_value <= 0.0
                  else max(0.0, export_budget) * net_price * wanted / total_value)
        bids.append(Bid(EDGE_EXTERNAL, good, area_of(good, port_tile), port_tile, 0.0, wanted,
                        net_price, EXTERNAL_BID_ELASTICITY, budget, maximum_price=net_price))
    return AgentOrders(bids=tuple(bids), offers=offers)


def actor_cargo_orders(landed_units: Mapping[GoodId, float], taken_units: Mapping[GoodId, float],
                       taken_limits: Mapping[GoodId, float], area_of: Callable[[GoodId, TileId], AreaId],
                       port_tile: TileId) -> AgentOrders:
    """The year's cargo that actors (the traders) carry, as orders at the port: an offer for each good landed here, at
    any price, and a bid for each good carried out, at up to the most per unit the actor can pay and still cover its
    carriage (without a ceiling a bid for more than the sellers hold has no price). The actor sizes its cargo by
    the price; the market only takes it in or gives it up."""
    offers = tuple(Offer(EDGE_EXTERNAL, good, area_of(good, port_tile), port_tile, units, 0.0)
                   for good, units in sorted(landed_units.items()) if units > 0.0)
    bids = tuple(Bid(EDGE_EXTERNAL, good, area_of(good, port_tile), port_tile, units, 0.0, 0.0, 0.0, float("inf"),
                     0, taken_limits[good])
                 for good, units in sorted(taken_units.items()) if units > 0.0 and taken_limits.get(good, 0.0) > 0.0)
    return AgentOrders(bids=bids, offers=offers)


def balance_of_payments(book: Book, currency: CurrencyId) -> BalanceOfPayments:
    """This year's money through the external edge, from the book's yearly edge records."""
    gross = book.edge_volume(EDGE_EXTERNAL, currency)
    net_paid_out = book.edge_net(EDGE_EXTERNAL, currency)     # edge paid in, less edge took out
    imports_paid = (gross - net_paid_out) / 2.0 if gross else 0.0
    exports_received = (gross + net_paid_out) / 2.0 if gross else 0.0
    return BalanceOfPayments(imports_paid, exports_received, imports_paid - exports_received)

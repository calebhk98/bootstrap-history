"""A stock-flow audit of the year's money: the supply change against what the edge accounts paid in
and took out, and the metal behind a metal-backed currency.

`Book.check_conservation` sums every purse, edge accounts included, so it is zero whatever happens; this
audit reads the supply without them. The residual is an identity (the book keeps it near zero), so
the findings that matter are the edge flows and the metal gap.
"""
import math
from dataclasses import dataclass, field
from typing import Dict, Tuple

from .merchants import EDGE_CARRIAGE
from .types import EDGE_LEGACY, EDGE_MINT, EDGE_WEAR, is_edge

# Edges that carry money only when something posts without naming its counterparty.
UNEXPECTED_MONEY_EDGES = (EDGE_LEGACY, EDGE_CARRIAGE)


@dataclass(frozen=True)
class MoneyAudit:
    supply_at_start: Dict[str, float]
    supply_at_end: Dict[str, float]
    edge_net: Dict[str, Dict[str, float]]          # edge account -> currency -> money it paid in, less taken out
    supply_change: Dict[str, float]
    residual: Dict[str, float]                      # supply change less the edges' net; identity, near zero
    metal_gap: Dict[str, float] = field(default_factory=dict)   # mint metal less (supply + wear not yet reconciled) times backing
    metal_awaiting_wear: Dict[str, float] = field(default_factory=dict)   # metal of the year's coin wear, booked after the mint's last reconciliation
    unexpected: Tuple[Tuple[str, str, float, float], ...] = ()  # (edge, currency, net, gross volume) on edges that should carry none

    @property
    def ok(self) -> bool:
        return not self.unexpected and all(abs(value) <= 1e-6 * max(1.0, abs(self.supply_at_end[currency]))
                                           for currency, value in self.residual.items())


def year_report(record) -> MoneyAudit:
    """The audit for the year the book has run since its last `start_year`."""
    book = record.book
    currencies = book.currencies()
    start = {currency: book.supply_at_start(currency) for currency in currencies}
    end = {currency: book.money_supply(currency) for currency in currencies}
    edges = {edge: {currency: book.edge_net(edge, currency) for currency in currencies if book.edge_volume(edge, currency)}
             for edge in book.edge_agents() if is_edge(edge)}
    change = {currency: end[currency] - start[currency] for currency in currencies}
    residual = {currency: change[currency] - math.fsum(nets.get(currency, 0.0) for nets in edges.values())
                for currency in currencies}
    unexpected = tuple((edge, currency, book.edge_net(edge, currency), book.edge_volume(edge, currency))
                       for edge in UNEXPECTED_MONEY_EDGES for currency in currencies if book.edge_volume(edge, currency) > 0.0)
    gap, awaiting = _metal_gap(record, end)
    return MoneyAudit(start, end, edges, change, residual, gap, awaiting, unexpected)


def _metal_gap(record, supply: Dict[str, float]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """(gap, metal awaiting wear). Coin wear is booked at year close, after the mint last matched its metal
    to the coin in circulation; the mint takes that metal out at its next reconciliation, early next year.
    The gap counts the worn coin as still embodied, so what is left is a real inconsistency; the metal
    of the worn coin is reported on its own."""
    spec = record.currency
    if spec.backing_good is None or spec.backing_per_unit <= 0.0:
        return {}, {}
    held = math.fsum(quantity for quantity in record.book.holdings(EDGE_MINT)["goods"].get(spec.backing_good, {}).values()
                     if quantity > 0.0)
    awaiting = max(0.0, -record.book.edge_net(EDGE_WEAR, spec.currency_id)) * spec.backing_per_unit
    embodied = supply.get(spec.currency_id, 0.0) * spec.backing_per_unit + awaiting
    return {spec.currency_id: held - embodied}, {spec.currency_id: awaiting}

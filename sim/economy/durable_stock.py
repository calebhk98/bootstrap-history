"""The stock of a durable a household wants in use, and how much of its holding is that stock.
Pure functions. The wanted stock is the expected flow it serves times the good's service life; the
flow is smoothed because a service life multiplies a one-year swing in spending many times over."""
from typing import Dict, Mapping

from sim.constants import declare

from .types import GoodId, GoodSpec

EXPECTED_SPENDING_ADJUSTMENT = declare(
    "EXPECTED_SPENDING_ADJUSTMENT", 0.3, kind="temporary_heuristic",
    unit="share of the gap closed a year", source=None, confidence="D",
    why="A household sizes the durables it wants in use on the spending it expects, which moves toward "
        "each year's actual spending by this share of the gap. Real households form expectations from "
        "income history and habit, which are not modelled; the share is an assumption.")


DURABLE_GAP_CLOSED_SHARE = declare(
    "DURABLE_GAP_CLOSED_SHARE", 0.4, kind="temporary_heuristic",
    unit="share of the gap to the wanted stock bought in a year", source=None, confidence="D",
    retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="A household replaces the wear of its durables each year and closes the rest of the gap to the stock it "
        "wants over several years, so its bid moves smoothly with its holding instead of alternating between "
        "nothing and the whole gap. How fast real households stock up is not modelled; the share is an assumption.")


def update_expected_spending(expected: float, spent: float, planned: float = 0.0) -> float:
    """Expected yearly spending after a year in which `spent` was spent (the first year seeds it). Money the
    household bid but the shops could not fill (`planned` above `spent`) is spending it set out to make: a year
    of rationing does not lower what it expects to spend, or the cap on a rise in its spending would ratchet
    down with the shortage."""
    spent = max(spent, planned)
    if expected <= 0.0:
        return spent
    return expected + EXPECTED_SPENDING_ADJUSTMENT * (spent - expected)


def expected_flow_scale(expected_spending: float, spending: float) -> float:
    """What share of a planned flow a durable's stock is sized on: expected spending over this year's."""
    if expected_spending <= 0.0 or spending <= 0.0:
        return 1.0
    return expected_spending / spending


def after_year_end_losses(serving_stock: float, spec: GoodSpec) -> float:
    """Stock at the next planning date: wear and spoilage both read the year's serving stock."""
    wear = min(1.0, 1.0 / spec.service_life_years) if spec.service_life_years > 0.0 else 0.0
    spoilage = min(1.0, max(0.0, spec.spoilage_per_year))
    return max(0.0, serving_stock * (1.0 - wear - spoilage))


def replacement_for_flow(flow: float, spec: GoodSpec) -> float:
    """Purchases that restore the serving stock from its solved year-end holding."""
    if spec.service_life_years <= 0.0:
        return flow
    serving = flow * spec.service_life_years
    return serving - after_year_end_losses(serving, spec)


def opening_stock_for_replacement(replacement: float, spec: GoodSpec) -> float:
    """The holding at a planning date that a yearly `replacement` keeps up: the serving stock the replacement
    restores, after its year-end losses."""
    loss_rate = min(1.0, min(1.0, 1.0 / spec.service_life_years) + min(1.0, max(0.0, spec.spoilage_per_year)))
    return after_year_end_losses(replacement / loss_rate, spec)


def purchase_toward_stock(flow: float, held: float, spec: GoodSpec) -> float:
    """Units of a durable bought in a year to serve `flow`: the replacement of the wear and spoilage the wanted
    stock suffers, plus a share of the gap between the holding and what the wanted stock leaves after its
    year-end losses. A holding at that level buys the replacement (so it is a fixed point of buying and
    losses), a larger one the replacement too (a household does not sell), and one below it closes
    a share of the gap each year, so a bid moves continuously with the holding."""
    if spec.service_life_years <= 0.0:
        return flow
    gap = max(0.0, after_year_end_losses(flow * spec.service_life_years, spec) - max(held, 0.0))
    return replacement_for_flow(flow, spec) + DURABLE_GAP_CLOSED_SHARE * gap


def in_use_stock(flow_by_good: Mapping[GoodId, float], specs: Mapping[GoodId, GoodSpec],
                 scale: float, band: float) -> Dict[GoodId, float]:
    """Stock of each durable the flow keeps in use (flow times service life, `band` added); the store
    does not count it as savings."""
    stock = {}
    for good, flow in flow_by_good.items():
        spec = specs.get(good)
        if spec is not None and spec.service_life_years > 0.0 and flow > 0.0:
            stock[good] = flow * scale * spec.service_life_years * (1.0 + band)
    return stock

"""The opening's leisure preference: the time split that makes the hours households offer equal the hours its runs hire.

An opening sized from final demand (opening_stationary.py) hires some hours a trade; the households' hours are what
the setup says a worker has. What the plot, household work and sale do not take is leisure, and the preference that
leaves exactly the hours hired for sale at the opening wage is solved here (Eurace initialises so that labour demand
equals supply; Caiani et al. 2016 solve the stationary state first). A trade whose workers have no hours to spare
(hired at least what is free) or that nobody hires gets no anchor, so its workers keep no leisure. Plain functions.
"""
import math
from typing import Dict, Mapping

from . import households_hours_offered
from .types import AgentId, Recipe


def hours_hired_by_trade(producers: Mapping[AgentId, object], recipes: Mapping[str, Recipe]) -> Dict[str, float]:
    """Hours a year the opening's producers hire in each trade at the runs they expect to work."""
    hours: Dict[str, list] = {}
    for producer in producers.values():
        for trade, per_run in recipes[producer.recipe_id].labour_hours.items():
            hours.setdefault(trade, []).append(producer.expected_sales * per_run)
    return {trade: math.fsum(rows) for trade, rows in sorted(hours.items())}


def anchors(supply, hired_by_trade: Mapping[str, float], price_level: float = 1.0) -> Dict[str, float]:
    """The anchor wage a trade (at the opening's price level) at which its workers sell the hours hired: the hours
    each offer leaves free at the wage it faces (`supply`, built with no leisure) against the hours hired; the
    difference is leisure, and only the hours the plot could not still use may be."""
    free: Dict[str, float] = {}
    eligible: Dict[str, float] = {}
    weighted_wage: Dict[str, float] = {}
    for offer in supply.offers:
        wage = supply.faced_wage.get((offer.trade, offer.area), offer.reservation_wage)
        _home, left, may_rest = supply.parts(offer, wage)
        free[offer.trade] = free.get(offer.trade, 0.0) + left
        eligible[offer.trade] = eligible.get(offer.trade, 0.0) + may_rest
        weighted_wage[offer.trade] = weighted_wage.get(offer.trade, 0.0) + may_rest * wage
    result: Dict[str, float] = {}
    for trade, hired in sorted(hired_by_trade.items()):
        if eligible.get(trade, 0.0) <= 0.0:
            continue
        anchor = households_hours_offered.leisure_anchor_wage(
            eligible[trade], free[trade] - hired, weighted_wage[trade] / eligible[trade])
        if anchor is not None and price_level > 0.0:
            result[trade] = anchor / price_level
    return result


def seed(economy) -> None:
    """Set the economy's leisure preference at its opening: the hours the households would sell after the plot and
    household work, against the hours the opening's producers hire. Left empty (no leisure) where nothing hires."""
    from . import year_labour
    setup, record = economy.setup, economy.record
    view = economy.view()
    outside = year_labour.outside_option_by_tile(setup, record, view)
    offers = year_labour.labour_offers(setup, record, view, outside)
    supply = economy._hour_supply(offers, view, outside, anchors={})
    record.leisure_anchor_wage = anchors(supply, hours_hired_by_trade(record.producers, setup.recipes),
                                         view.chained_price_level(setup.currency_id))

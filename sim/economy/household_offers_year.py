"""The household decisions over the year's offers as rows: the work a cohort hires and does itself (`household_work_year.decide`) and
the hours it keeps for its plot (`household_hours_year.plot_parameters_by_cohort`), with the offers read as columns
(`household_offer_reads.OfferReads`) rather than as `LabourOffer` records. Each answer equals the record version's, to the last digit.
A set of offers holding a NaN or infinite figure takes the record version."""
from typing import Dict, Mapping, Optional, Sequence, Tuple

from . import cohort_prime, household_hours_year, household_work_year, households_basket, households_cohort, households_work, labour_state
from .cohort_store import table_of
from .household_offer_reads import OfferReads
from .labour_ask_floor import hectares_per_hour_by_recipe
from .labour_offer_rows import LabourOfferRows
from .labour_offers_table import PlotParameters
from .market_memory import market_key
from .types import AgentId


def lacks_history(record, reads: OfferReads) -> bool:
    """`household_work_year.lacks_history`: whether some offer is in a labour market no year has yet shown the households."""
    history = record.labour.sold_share_expected
    return any(market_key(trade, area) not in history for trade, area in reads.markets)


def expected_shares(setup, record, reads: OfferReads) -> Dict[Tuple[str, str], float]:
    """`household_work_year.expected_shares`: {(trade, area): share of the offered hours its producers' planned runs hire}."""
    needed = labour_state.producers_hours_needed(setup, record)
    return {(trade, area): households_work.expected_sold_share(needed.get(area, {}).get(trade, 0.0), hours)
            for (trade, area), hours in reads.hours_by_market().items()}


def hour_values(setup, record, view, reads: OfferReads, expected: Mapping[Tuple[str, str], float]) -> Dict[str, float]:
    """{cohort id: worth of an hour of its own} (`households_work.hour_value` over its offers at the faced wage times the share
    its market is expected to sell); a cohort with no offers is not in it."""
    faced = reads.faced_wage(view.wage)
    share = reads.market_values(lambda trade, area: household_work_year.sold_share_at(record, trade, area, expected.get((trade, area), 1.0)))
    values = reads.hour_value_of_workers(faced, share).tolist()
    return {name: values[number] for number, name in enumerate(reads.rows.workers.names)}


def plans(setup, record, view, reads: OfferReads) -> Dict[AgentId, Tuple[float, float, Tuple[str, ...]]]:
    """`household_work_year.plans` with no service-price floors: each cohort's (hours hired a person, hours done itself, grains
    bought milled) for the year; changes nothing."""
    expected = expected_shares(setup, record, reads) if setup.household_work and lacks_history(record, reads) else {}
    cohort_prime.prime_food_baskets(setup, record, view)
    values = hour_values(setup, record, view, reads, expected) if setup.household_work else {}
    result: Dict[AgentId, Tuple[float, float, Tuple[str, ...]]] = {}
    store = table_of(record.cohorts)
    for cohort in store.figures(store.order()):
        cohort_id = cohort.agent_id
        if not setup.household_work:
            hired, own, milled = 0.0, 0.0, ()
        else:
            value, needed, price, milled = household_work_year.work_terms_at(setup, record, view, cohort, values.get(cohort.agent_id, 0.0))
            hired, own, milled = household_work_year.planned_hours(needed, value, price, 0.0, milled,
                                                                  household_work_year.whole_servant_terms(setup, cohort))
        result[cohort_id] = (hired / cohort.people if cohort.people > 0.0 else 0.0, own, milled)
    return result


def decide(setup, record, view, rows: LabourOfferRows) -> Dict[AgentId, float]:
    """`household_work_year.decide` over the rows: store each cohort's hired hours a person and the grains it buys milled, and
    return the own hours of each cohort, which it keeps back from the market."""
    reads = OfferReads(rows)
    if not reads.exact:
        return household_work_year.decide(setup, record, view, rows.objects())
    if setup.household_work and lacks_history(record, reads):
        for (trade, area), share in sorted(expected_shares(setup, record, reads).items()):
            record.labour.expect_sold_share(market_key(trade, area), share)
    decided = plans(setup, record, view, reads)
    households_cohort.set_work_plans(record.cohorts, decided)
    return {cohort_id: own for cohort_id, (_per_person, own, _milled) in decided.items()}


def plot_parameters_by_cohort(setup, record, view, rows: LabourOfferRows, options: Mapping[str, Sequence],
                              hectares_held: Mapping[AgentId, float]) -> Dict[AgentId, PlotParameters]:
    """`household_hours_year.plot_parameters_by_cohort` with the hours each cohort offers summed from the rows."""
    reads = OfferReads(rows)
    if not reads.exact:
        return household_hours_year.plot_parameters_by_cohort(setup, record, view, rows.objects(), options, hectares_held)
    offered = reads.hours_of_workers().tolist()
    hectares_per_hour = hectares_per_hour_by_recipe(setup.recipes, setup.land_per_run)
    parameters: Dict[AgentId, PlotParameters] = {}
    priced_by_tile: Dict[str, list] = {}
    store = table_of(record.cohorts)
    for cohort in store.figures(store.order()):
        cohort_id = cohort.agent_id
        number: Optional[int] = reads.worker_number(cohort_id)
        if cohort.tile not in priced_by_tile:
            priced_by_tile[cohort.tile] = households_basket.tile_need_prices(setup, view, cohort.tile)
        found = household_hours_year.cohort_plot_parameters(
            setup, cohort, offered[number] if number is not None else 0.0, priced_by_tile[cohort.tile], options,
            hectares_held.get(cohort_id, 0.0), hectares_per_hour)
        if found is not None:
            parameters[cohort_id] = found
    return parameters

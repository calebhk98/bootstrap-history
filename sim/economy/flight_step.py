"""The economy's year step for taxed people: who fled, what land they left, who came home (flight_year.py)."""
import dataclasses
import math
from typing import Dict, Mapping

from sim.labour.api import people_in

from . import flight_routes, flight_year
from .labour_inputs import TONNES_CARRIED_PER_MIGRANT
from .setup import area_tile, labour_area


def people_before(setup, record) -> Dict[str, float]:
    """People in each labour area before the year's market moves them; empty when the state takes nothing to flee from."""
    return {area: people_in(record.labour.workforce, area) for area in record.labour.workforce.workers}


def cohorts_follow_workers(record, change_by_area: Mapping[str, float], people_by_area: Mapping[str, float]) -> None:
    """The households of an area gain or lose people with the workers who moved in or out: each cohort is scaled by the
    area's net change over the people it held before (`people_before`)."""
    for cohort_id, cohort in sorted(record.cohorts.items()):
        area = labour_area(cohort.tile)
        before = people_by_area.get(area, 0.0)
        change = change_by_area.get(area, 0.0)
        if before > 0.0 and change != 0.0:
            scale = max(0.0, 1.0 + change / before)
            record.cohorts[cohort_id] = dataclasses.replace(cohort, people=cohort.people * scale,
                                                            working_people=cohort.working_people * scale)


def mean_year_income(workforce, hours_per_worker_year: float) -> Dict[str, float]:
    """A year's hours at the mean of the wages each area's trades last settled at."""
    return {area: hours_per_worker_year * sum(wages.values()) / len(wages)
            for area, wages in sorted(workforce.wages.items()) if wages}


def settle(setup, record, inputs, report, before, context, carriage) -> Dict[str, float]:
    """After the year's labour market: tenants of areas people left leave their land, the leavers join the fugitives, and
    fugitives for whom home now beats the refuge come back. Returns the people who came home by area. `inputs` carries the
    state's take, its amnesty and its immunity (`YearInputs`); `context` is the year's labour inputs (subsistence, routes)."""
    cohorts_follow_workers(record, report.migrated, before)
    subsistence = context.subsistence_per_worker_year
    taxed = flight_routes.taxed_share_by_area(inputs.taxed_share_by_tile)
    if setup.flight is None or (not taxed and not record.unfree.fugitives):
        return {}
    income = mean_year_income(record.labour.workforce, setup.working_hours_per_year)
    shares = flight_year.fleeing_shares(report.migrated, before, flight_year.tax_attributable_fractions(context.routes, taxed, income, subsistence))
    flight_year.note_fugitives(record.unfree.fugitives, shares, before, report.migrated, taxed, subsistence)
    flight_year.tenants_flee(record, shares)

    def moving_cost(refuge: str, home: str) -> float:
        cost = carriage.cost_per_tonne(area_tile(refuge), area_tile(home)) * TONNES_CARRIED_PER_MIGRANT
        return cost if math.isfinite(cost) else math.inf

    after_market = people_before(setup, record)
    came = flight_year.return_fugitives(
        record.labour.workforce, record.unfree.fugitives, taxed, subsistence, income,
        inputs.amnesty_share, inputs.immunity_years, moving_cost, setup.flight.arrears_owed_by_fugitive, setup.flight.share_after_immunity)
    after_return = people_before(setup, record)
    cohorts_follow_workers(record, {area: after_return.get(area, 0.0) - people for area, people in after_market.items()}, after_market)
    return came

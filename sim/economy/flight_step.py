"""The economy's year step for taxed people: who fled, what land they left, who came home (flight_year.py). The workers' moves
are reported (`report.migrated`), not written to the households: demography owns people and moves them (`MovePeople`)."""
import math
from typing import Dict

from sim.labour.api import people_in

from . import flight_routes, flight_year
from .labour_inputs import TONNES_CARRIED_PER_MIGRANT
from .setup import area_tile


def people_before(labour) -> Dict[str, float]:
    """People now in each labour area that has workers."""
    return {area: people_in(labour.workforce, area) for area in labour.workforce.workers}


def mean_year_income(workforce, hours_per_worker_year: float) -> Dict[str, float]:
    """A year's hours at the mean of the wages each area's trades last settled at, weighted by the people working each
    trade there (the plain mean where nobody works any of them, so a trade nobody works does not set the area's income)."""
    income: Dict[str, float] = {}
    for area, wages in sorted(workforce.wages.items()):
        if not wages:
            continue
        trades = sorted(wages)
        people = [math.fsum(workforce.workers.get(area, {}).get(trade, ())) for trade in trades]
        total = math.fsum(people)
        if total > 0.0:
            mean = math.fsum(wages[trade] * count for trade, count in zip(trades, people)) / total
        else:
            mean = math.fsum(wages[trade] for trade in trades) / len(trades)
        income[area] = hours_per_worker_year * mean
    return income


def settle(setup, record, inputs, report, before, context, carriage) -> Dict[str, float]:
    """After the year's labour market: tenants of areas people left leave their land, the leavers join the fugitives, and
    fugitives for whom home now beats the refuge come back. Returns the people who came home by area. `inputs` carries the
    state's take, its amnesty and its immunity (`EconomyYearInputs`); `context` is the year's labour inputs (subsistence, routes)."""
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

    after_market = people_before(record.labour)
    came = flight_year.return_fugitives(
        record.labour.workforce, record.unfree.fugitives, taxed, subsistence, income,
        inputs.amnesty_share, inputs.immunity_years, moving_cost, setup.flight.arrears_owed_by_fugitive, setup.flight.share_after_immunity)
    after_return = people_before(record.labour)
    add_returners(report.migrated, after_market, after_return)
    return came


def add_returners(migrated: Dict[str, float], after_market: Dict[str, float], after_return: Dict[str, float]) -> None:
    """Add to `migrated` (net move by area) the people who came home: those who came home are moves too, and demography
    takes the net with the market's. An area with no workers until the returners arrived has no row after the market."""
    for area in sorted(set(after_market) | set(after_return)):
        migrated[area] = migrated.get(area, 0.0) + after_return.get(area, 0.0) - after_market.get(area, 0.0)

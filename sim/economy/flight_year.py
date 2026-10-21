"""The year's flight and return of taxed people (Complaint 657), after the labour market has moved workers.

People leave a taxed area through the migration rule; the tenants of that area leave the land they worked in the same share
(`titles_flight.tenant_flees`), and the people who left are remembered as fugitives with what they owe. A fugitive
returns by the same rule run backwards: his income where he is against his income at home after the state's take,
less the arrears he owes on coming home (the state's amnesty waives a share; its immunity lifts the take on the land
he takes up again for its years).
"""
import math
from typing import Any, Callable, Dict, Mapping

from sim.labour.api import migration_shares, people_in

from .setup import labour_area
from .titles_flight import tenant_flees


def tax_attributable_fractions(routes: Mapping[str, Any], taxed_by_area: Mapping[str, float],
                               year_income_by_area: Mapping[str, float],
                               subsistence_by_area: Mapping[str, float]) -> Dict[str, float]:
    """For each area, the share of the people leaving it that the state's take accounts for: one less the flow the migration
    rule gives with no take and no recapture penalty over the flow it gives with them, on the area's routes at the year's
    incomes. Zero where the take changes nothing."""
    taxed = real_income_by_area(year_income_by_area, taxed_by_area, subsistence_by_area)
    free = real_income_by_area(year_income_by_area, {}, subsistence_by_area)
    fractions: Dict[str, float] = {}
    for origin, ways in routes.items():
        floor = subsistence_by_area.get(origin, 0.0)
        if floor <= 0.0 or origin not in taxed or taxed_by_area.get(origin, 0.0) <= 0.0:
            continue
        with_take = sum(migration_shares(taxed[origin], [(taxed.get(way.destination), (way.moving_cost + way.expected_penalty) / floor)
                                                         for way in ways]))
        without = sum(migration_shares(free[origin], [(free.get(way.destination), way.moving_cost / floor) for way in ways]))
        if with_take > 0.0:
            fractions[origin] = max(0.0, min(1.0, 1.0 - without / with_take))
    return fractions


def fleeing_shares(migrated: Mapping[str, float], people_before: Mapping[str, float],
                   attributable: Mapping[str, float]) -> Dict[str, float]:
    """Share of an area's people who left it this year because of the state's take: the part of the net outflow that
    `attributable` (tax_attributable_fractions) gives to it."""
    shares: Dict[str, float] = {}
    for area, change in migrated.items():
        before = people_before.get(area, 0.0)
        if change < 0.0 and before > 0.0 and attributable.get(area, 0.0) > 0.0:
            shares[area] = min(1.0, -change * attributable[area] / before)
    return shares


def note_fugitives(fugitives: Dict[str, Dict[str, Any]], shares: Mapping[str, float], people_before: Mapping[str, float],
                   migrated: Mapping[str, float], taxed_by_area: Mapping[str, float],
                   subsistence_by_area: Mapping[str, float]) -> None:
    """Add this year's leavers to the fugitives of their area, and a year's tax unpaid to what each head owes (the take of
    a year at his area's subsistence for each year he is away). The refuge is where most arrived."""
    refuge = max(sorted(migrated), key=lambda area: migrated[area], default=None)
    for area in sorted(set(fugitives) | set(shares)):
        row = fugitives.setdefault(area, {"people": 0.0, "arrears_per_head": 0.0, "refuge": refuge})
        row["arrears_per_head"] = row["arrears_per_head"] + taxed_by_area.get(area, 0.0) * subsistence_by_area.get(area, 0.0)
        left = shares.get(area, 0.0) * people_before.get(area, 0.0)
        row["people"] += left
        if left > 0.0 and refuge is not None:
            row["refuge"] = refuge


def tenants_flee(record, shares_by_area: Mapping[str, float]) -> Dict[str, float]:
    """The tenants of each fleeing area leave their land in that share; the share released per tile."""
    released: Dict[str, float] = {}
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        share = shares_by_area.get(labour_area(cohort.tile), 0.0)
        if share > 0.0:
            for tile, left in tenant_flees(record, cohort.agent_id, share).items():
                released[tile] = released.get(tile, 0.0) + left
    return released


def returning_share(real_income_away: float, real_income_home: float, arrears_owed: float, subsistence: float,
                    moving_cost: float) -> float:
    """Share of fugitives who come home this year: the migration rule with home as the one route, its cost the move and the
    arrears owed, in years of subsistence. Zero when an income cannot be weighed."""
    if real_income_away <= 0.0 or real_income_home <= 0.0 or subsistence <= 0.0:
        return 0.0
    return migration_shares(real_income_away, [(real_income_home, (moving_cost + arrears_owed) / subsistence)])[0]


def real_income_by_area(year_income_by_area: Mapping[str, float], taxed_by_area: Mapping[str, float],
                        subsistence_by_area: Mapping[str, float]) -> Dict[str, float]:
    """Year's income over subsistence after the state's take; an area with no income or no subsistence is left out."""
    return {area: (1.0 - min(1.0, taxed_by_area.get(area, 0.0))) * income / subsistence_by_area[area]
            for area, income in year_income_by_area.items() if income > 0.0 and subsistence_by_area.get(area, 0.0) > 0.0}


def move_back(workforce, refuge: str, home: str, count: float) -> float:
    """Take `count` people out of the refuge's workers, in proportion across its trades and bands, and put them in the home
    area's; returns the number moved (no more than the refuge holds)."""
    held = people_in(workforce, refuge, include_trainees=False)
    if held <= 0.0 or count <= 0.0:
        return 0.0
    fraction = min(1.0, count / held)
    for trade, bands in sorted(workforce.workers.get(refuge, {}).items()):
        home_bands = workforce.workers.setdefault(home, {}).setdefault(trade, [0.0] * len(bands))
        for band, amount in enumerate(bands):
            moved = amount * fraction
            bands[band] -= moved
            home_bands[band] += moved
    return held * fraction


def return_fugitives(workforce, fugitives: Dict[str, Dict[str, Any]], taxed_by_area: Mapping[str, float],
                     subsistence_by_area: Mapping[str, float], year_income_by_area: Mapping[str, float],
                     amnesty_share: float, immunity_years: float, moving_cost: Callable[[str, str], float],
                     arrears_owed: Callable[[float, float], float],
                     take_after_immunity: Callable[[float, float, float], float]) -> Dict[str, float]:
    """Run the return: each home area's fugitives weigh their refuge against home. A returner takes up land at home, so the
    take he weighs is the immunity rule's (`take_after_immunity(take, years since taking up, immunity years)`, none
    in his first years back). Returns the people who came home by area."""
    taxed_home = {area: take_after_immunity(taxed_by_area.get(area, 0.0), 0.0, immunity_years) for area in fugitives}
    at_home = real_income_by_area(year_income_by_area, {**taxed_by_area, **taxed_home}, subsistence_by_area)
    away = real_income_by_area(year_income_by_area, taxed_by_area, subsistence_by_area)
    came: Dict[str, float] = {}
    for home in sorted(fugitives):
        row = fugitives[home]
        refuge = row.get("refuge")
        if row["people"] <= 0.0 or refuge is None or refuge == home:
            continue
        cost = moving_cost(refuge, home)
        if not math.isfinite(cost):
            continue
        share = returning_share(away.get(refuge, 0.0), at_home.get(home, 0.0), arrears_owed(row["arrears_per_head"], amnesty_share),
                                subsistence_by_area.get(home, 0.0), cost)
        moved = move_back(workforce, refuge, home, row["people"] * share)
        if moved > 0.0:
            row["people"] -= moved
            came[home] = moved
    for home in [area for area, row in fugitives.items() if row["people"] <= 1e-9]:
        del fugitives[home]
    return came

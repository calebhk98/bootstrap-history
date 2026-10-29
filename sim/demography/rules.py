"""Demography's rules as plain functions of plain values: who the nation's people are by age, what they ate, a mass-mortality
cut across the cohorts, the wage premium a shortfall of people makes, the record of a year."""
import math

from sim.unit_conversions import PERCENT_SCALE
from sim.world.demography import (CHILD_CALORIE_EQUIVALENT, ELDERLY_CALORIE_EQUIVALENT,
                                  SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY)

# years between two wage-cascade notes, and the premium (percent) under which a wage rise is not worth saying
WAGE_CASCADE_NOTE_SPACING_YEARS = 15
WAGE_CASCADE_NOTE_MINIMUM_PERCENT = 0.5


def adult_equivalents(population):
    """`population`'s food need in adult-equivalent units: the weighting `Population.nutrition_ratio` uses, so there is no
    second opinion on what a person is worth in calories."""
    return (population.children * CHILD_CALORIE_EQUIVALENT
            + population.working_age
            + population.elderly * ELDERLY_CALORIE_EQUIVALENT)


def pop_scale(total_people, reference_people, floor):
    """The nation's people against the reference population, never below `floor`."""
    return max(floor, total_people / reference_people)


def population_seed(civilisation_id):
    """A seed for the nation's `Population`, from the civilisation's id: the same on every process, different between
    civilisations."""
    return sum((index + 1) * ord(character) for index, character in enumerate(str(civilisation_id))) % (2 ** 32)


def cut_cohorts(population, raw, vulnerability_child, vulnerability_working_age, vulnerability_elderly):
    """Cut the cohorts of `population` unevenly by age so the population-weighted average loss equals `raw`
    (a fraction of the whole), each cohort losing at most all of itself."""
    weighted = (population.children * vulnerability_child
                + population.working_age * vulnerability_working_age
                + population.elderly * vulnerability_elderly)
    if weighted <= 0.0 or raw <= 0.0:
        return
    scale = raw * population.total / weighted
    population.children -= population.children * min(1.0, scale * vulnerability_child)
    population.working_age -= population.working_age * min(1.0, scale * vulnerability_working_age)
    population.elderly -= population.elderly * min(1.0, scale * vulnerability_elderly)


def national_eaten_over_need(accounts):
    """People-weighted food eaten per head over the hunger need's floor across every cohort of the year's
    accounts; None when no cohort has a hunger need."""
    people = math.fsum(cohort.people for cohort in accounts.cohorts)
    need = math.fsum(cohort.people * cohort.need_per_head for cohort in accounts.cohorts)
    if people <= 0.0 or need <= 0.0:
        return None
    return math.fsum(cohort.people * cohort.eaten_per_head for cohort in accounts.cohorts) / need


def eaten_over_need_by_tile(accounts):
    """Each tile's food eaten per head over its need, for the tiles with a hunger need."""
    return {tile.tile: tile.eaten_over_need for tile in accounts.tiles if tile.need_per_head > 0.0}


def food_kcal_per_day(eaten_over_need, adult_equivalent_population):
    """The calories a day that feed `adult_equivalent_population` exactly at `eaten_over_need` of its need."""
    return eaten_over_need * adult_equivalent_population * SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY


def wage_cascade(wage_index, wage_index_base, elasticity):
    """(wage premium in percent, share of the people short of trend) behind a wage index above its base. The shortfall is
    recovered from the premium so the note and the index cannot drift apart."""
    premium = (wage_index / wage_index_base - 1.0) * PERCENT_SCALE
    shortfall = (premium / PERCENT_SCALE) / elasticity if elasticity else 0.0
    return premium, shortfall


def wage_cascade_due(premium_percent, year, year_last_said):
    """Whether a premium is worth a note this year: above the minimum, and a note's spacing since the last."""
    return premium_percent > WAGE_CASCADE_NOTE_MINIMUM_PERCENT and year - year_last_said >= WAGE_CASCADE_NOTE_SPACING_YEARS


def yearly_record_row(year, total_people, flows):
    """One year's entry of the demographic record."""
    return {"year": year, "population": round(total_people, 1), "births": round(flows.births),
            "deaths": round(flows.deaths), "nutrition_ratio": round(flows.nutrition_ratio, 4)}


def deaths_with_externalities(deaths_by_band, answers):
    """`deaths_by_band` plus the deaths each externality answer (`{"deaths_by_band": {band: people}, ...}`, or None) adds,
    band by band and never negative; the same mapping when nothing answered."""
    if not answers:
        return deaths_by_band
    total = {band: float(count) for band, count in deaths_by_band.items()}
    for answer in answers:
        for band, count in ((answer or {}).get("deaths_by_band") or {}).items():
            total[band] = total.get(band, 0.0) + max(0.0, float(count))
    return total


def nutrition_ratio_of(flows):
    """The share of the people's food need a yearly step's flows say was met, or None before a year has been stepped."""
    return None if flows is None else float(flows.nutrition_ratio)

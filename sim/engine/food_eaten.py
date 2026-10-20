"""What the nation's households ate last year, from the agent economy's accounts, as the food demography feeds on.

The economy books food eaten per cohort (`sim/economy/year_accounts.py`). The nation's people-weighted eaten
over need is kept in `state.population.food_eaten_over_need` when the economy's year closes, and the
next year's step turns it into the calories a day it is fed. Each tile's figure is kept too, and feeds that tile's
region (`sim/engine/regional_people.py`). While no economy
year has closed (a game just opened, or a game whose economy never ran) nothing is recorded and the engine's
farm path (`Sim._demographic_recovery`) supplies the food.
"""
import math

from sim.world import demography


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
    return eaten_over_need * adult_equivalent_population * demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY


class FoodEatenMixin:

    def record_food_eaten(self, outcome):
        """Keep the year's national food eaten over need from the economy's outcome, for the next demographic step."""
        accounts = getattr(outcome, "accounts", None)
        self.state.population.food_eaten_over_need = (
            None if accounts is None else national_eaten_over_need(accounts))
        self.state.population.regional_eaten_over_need = (
            {} if accounts is None else eaten_over_need_by_tile(accounts))

    def household_food_kcal_per_day(self, adult_equivalent_population):
        """Calories a day the households ate last year at this population's size, or None before an economy year closed."""
        eaten_over_need = self.state.population.food_eaten_over_need
        return None if eaten_over_need is None else food_kcal_per_day(eaten_over_need, adult_equivalent_population)

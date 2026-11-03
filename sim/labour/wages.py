"""The opening wage schedule: a money value for one labour hour and a training
premium, held above a subsistence floor.

    wage(trade) = max(floor, money_per_labour_hour * premium(trade))

The money value of a labour hour is anchored outside this module (to the
civilisation's coin). The floor is what one working hour must earn to keep a
worker and the people who depend on that worker fed: the basket's cost in
labour hours per hour worked, times the money value of an hour. The premium
repays the years a trade takes to learn. Once the economy has opened its
labour markets set the wages and this schedule is only the fallback.

Nothing here knows about any civilisation or actor: a `WageSchedule` is built
from plain numbers, so any actor that owns a workforce can own one.
"""
import copy
from typing import Any, Dict, Iterable, Mapping

from sim.constants import declare
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

from .market import premium as market_premium


CAREER_YEARS = declare(
    "CAREER_YEARS", 30.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Working career over which a trade's training years are repaid. "
        "To be replaced by the demography model's expected working life.")

NON_FOOD_SUBSISTENCE_MARKUP = declare(
    "NON_FOOD_SUBSISTENCE_MARKUP", 1.5, kind="temporary_heuristic",
    unit="subsistence spending per unit of food spending", source=None,
    confidence="D",
    why="Housing, clothing and fuel on top of food when finding what a "
        "worker must earn. Chosen before any wage was compared; to be "
        "replaced by a subsistence basket priced through the same solver.")


def training_premium(training_years: float, discount_rate: float,
                     career_years: float = CAREER_YEARS) -> float:
    """Wage multiple that leaves a trainee indifferent to skipping training (market/premium.py)."""
    return market_premium.training_premium(training_years, discount_rate, career_years)


def subsistence_wage_per_hour(food_kg_per_person_year: float,
                              food_price_per_kg: float,
                              people_fed_per_worker: float,
                              non_food_markup: float = NON_FOOD_SUBSISTENCE_MARKUP,
                              hours_per_year: float = HOURS_PER_PERSON_YEAR) -> float:
    """What one working hour must earn to keep a worker and dependants, in
    the unit the food price is given in (labour hours give labour hours)."""
    yearly_need = (food_kg_per_person_year * food_price_per_kg
                   * people_fed_per_worker * non_food_markup)
    return yearly_need / hours_per_year


class WageSchedule(object):
    """Wages per hour for every trade of one labour market.

    `money_per_labour_hour` is what an hour of the unskilled numeraire trade
    is worth in money; `subsistence_hours_per_hour` is the basket's cost in
    such hours per hour worked. The schedule is immutable once built;
    `priced_at` answers the same schedule at another money value.
    """

    def __init__(self, training_years: Mapping[str, float], money_per_labour_hour: float,
                 subsistence_hours_per_hour: float, discount_rate: float,
                 career_years: float = CAREER_YEARS,
                 hours_per_year: float = HOURS_PER_PERSON_YEAR) -> None:
        self.money_per_labour_hour = money_per_labour_hour
        self.subsistence_hours_per_hour = subsistence_hours_per_hour
        self.hours_per_year = hours_per_year
        self.training_years = dict(training_years)
        self._premium = {trade: training_premium(years, discount_rate, career_years)
                         for trade, years in training_years.items()}

    @property
    def floor_per_hour(self) -> float:
        return self.subsistence_hours_per_hour * self.money_per_labour_hour

    def trades(self) -> Iterable[str]:
        return self._premium.keys()

    def premium(self, trade: str) -> float:
        return self._premium.get(trade, 1.0)

    def wage_per_hour(self, trade: str) -> float:
        wage = self.money_per_labour_hour * self.premium(trade)
        # Anyone can fall back to unskilled work, so nothing pays below the floor.
        return max(self.floor_per_hour, wage)

    def annual_wage(self, trade: str) -> float:
        return self.wage_per_hour(trade) * self.hours_per_year

    def wages_per_hour(self) -> Dict[str, float]:
        return {trade: self.wage_per_hour(trade) for trade in sorted(self._premium)}

    def priced_at(self, money_per_labour_hour: float) -> "WageSchedule":
        """This schedule with an hour of the unskilled trade worth `money_per_labour_hour`; this one is unchanged."""
        priced = copy.copy(self)
        priced.money_per_labour_hour = money_per_labour_hour
        return priced

    def document(self) -> Dict[str, Any]:
        """The wage table in the shape the price solver reads, with the money
        value of a labour hour that turns its labour-hour prices into money."""
        return {"wage_rates_denarii_per_hour":
                {trade: {"rate": wage} for trade, wage in self.wages_per_hour().items()},
                "money_per_labour_hour": self.money_per_labour_hour}

    def ratio_document(self) -> Dict[str, Any]:
        """The same shape in numeraire units, before any floor:
        the training premium alone, with one labour hour worth one unit."""
        return {"wage_rates_denarii_per_hour":
                {trade: {"rate": premium} for trade, premium in sorted(self._premium.items())},
                "money_per_labour_hour": 1.0}

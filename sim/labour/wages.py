"""Wages from the labour market: a money value for one labour hour, a training
premium and a tightness adjustment, held above a subsistence floor.

    wage(trade) = max(floor, money_per_labour_hour * premium(trade) * tightness_factor(trade))

The money value of a labour hour is anchored outside this module (to the
civilisation's coin). The floor is what one working hour must earn to keep a
worker and the people who depend on that worker fed: the basket's cost in
labour hours per hour worked, times the money value of an hour. The premium
repays the years a trade takes to learn. The tightness factor moves a little
each year toward the trades whose need exceeds their hours and away from those
with slack.

Nothing here knows about any civilisation or actor: a `WageSchedule` is built
from plain numbers, so any actor that owns a workforce can own one.
"""
import math
from typing import Any, Dict, Iterable, Mapping, Optional

from sim.constants import declare

UNSKILLED_TRADE = "labourer"

HOURS_PER_WORKER_YEAR = declare(
    "HOURS_PER_WORKER_YEAR", 2000.0, kind="engineering_estimate",
    unit="hours/worker/year", source=None, confidence="C",
    why="Converts an hourly wage to an annual one. Same order as the "
        "household's own person-year (a ten-hour day for most of the year "
        "less feast days).")

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

TIGHTNESS_ADJUSTMENT_RATE_PER_YEAR = declare(
    "TIGHTNESS_ADJUSTMENT_RATE_PER_YEAR", 0.05, kind="temporary_heuristic",
    unit="fractional wage change per year per unit of relative gap",
    source=None, confidence="D",
    why="How fast a wage follows the gap between the hours a trade needs and "
        "the hours it has. Gradual, in the manner of Lengnick and EURACE "
        "wage-setting; not fitted to any observed wage path.")

TIGHTNESS_GAP_LIMIT = declare(
    "TIGHTNESS_GAP_LIMIT", 1.0, kind="temporary_heuristic",
    unit="relative gap (need/have - 1)", source=None, confidence="D",
    why="Largest relative gap that moves a wage in one year, so an absent "
        "trade or a collapse in hours cannot jump a wage.")

TIGHTNESS_REVERSION_RATE_PER_YEAR = declare(
    "TIGHTNESS_REVERSION_RATE_PER_YEAR", 0.03, kind="temporary_heuristic",
    unit="fraction of the distance back to 1.0 per year", source=None,
    confidence="D",
    why="Without it a scarcity premium never leaves once the gap closes. "
        "Stands in for the bargaining that fades when workers are no "
        "longer hard to find; not fitted to any observed wage path.")

MIN_TIGHTNESS_FACTOR = declare(
    "MIN_TIGHTNESS_FACTOR", 0.5, kind="temporary_heuristic",
    unit="multiple of the untightened wage", source=None, confidence="D",
    why="Slack cannot push a trade's premium below this share of itself.")

MAX_TIGHTNESS_FACTOR = declare(
    "MAX_TIGHTNESS_FACTOR", 3.0, kind="temporary_heuristic",
    unit="multiple of the untightened wage", source=None, confidence="D",
    why="Scarcity cannot push a trade's wage above this multiple of itself.")


def training_premium(training_years: float, discount_rate: float,
                     career_years: float = CAREER_YEARS) -> float:
    """Wage multiple that leaves a trainee indifferent to skipping training.

    An unskilled worker earns the unit wage for the whole career. A trainee
    earns nothing for `training_years`, then the premium for the rest, with
    both streams discounted continuously. Zero training gives exactly 1.
    """
    training_years = min(max(0.0, training_years), career_years * 0.9)
    if training_years == 0.0:
        return 1.0
    discounted_career = 1.0 - math.exp(-discount_rate * career_years)
    discounted_after_training = (math.exp(-discount_rate * training_years)
                                 - math.exp(-discount_rate * career_years))
    return discounted_career / discounted_after_training


def subsistence_wage_per_hour(food_kg_per_person_year: float,
                              food_price_per_kg: float,
                              people_fed_per_worker: float,
                              non_food_markup: float = NON_FOOD_SUBSISTENCE_MARKUP,
                              hours_per_year: float = HOURS_PER_WORKER_YEAR) -> float:
    """What one working hour must earn to keep a worker and dependants, in
    the unit the food price is given in (labour hours give labour hours)."""
    yearly_need = (food_kg_per_person_year * food_price_per_kg
                   * people_fed_per_worker * non_food_markup)
    return yearly_need / hours_per_year


def training_years_with_family_default(registry_training: Mapping[str, Optional[float]],
                                       family_of: Mapping[str, str]) -> Dict[str, float]:
    """Years per trade; a trade that states none takes its family's median."""
    known_by_family: Dict[str, list] = {}
    for trade, years in registry_training.items():
        if years is not None:
            known_by_family.setdefault(family_of.get(trade, ""), []).append(years)
    resolved = {}
    for trade, years in registry_training.items():
        if years is None:
            family_years = sorted(known_by_family.get(family_of.get(trade, ""), [0.0]))
            years = family_years[len(family_years) // 2]
        resolved[trade] = float(years)
    return resolved


def adjusted_tightness_factor(factor: float, hours_required: float,
                              hours_have: float) -> float:
    """One year's move of a trade's tightness factor."""
    if hours_have <= 0.0:
        if hours_required <= 0.0:
            return factor
        gap = TIGHTNESS_GAP_LIMIT
    else:
        gap = hours_required / hours_have - 1.0
    gap = max(-TIGHTNESS_GAP_LIMIT, min(TIGHTNESS_GAP_LIMIT, gap))
    moved = factor * (1.0 + TIGHTNESS_ADJUSTMENT_RATE_PER_YEAR * gap)
    moved += (1.0 - moved) * TIGHTNESS_REVERSION_RATE_PER_YEAR
    return max(MIN_TIGHTNESS_FACTOR, min(MAX_TIGHTNESS_FACTOR, moved))


class WageSchedule(object):
    """Wages per hour for every trade of one labour market.

    `money_per_labour_hour` is what an hour of the unskilled numeraire trade
    is worth in money; `subsistence_hours_per_hour` is the basket's cost in
    such hours per hour worked. `tightness_factors` is the only state and is
    owned by the caller so it can live in a save; a trade missing from it is
    at 1.0.
    """

    def __init__(self, training_years: Mapping[str, float], money_per_labour_hour: float,
                 subsistence_hours_per_hour: float, discount_rate: float,
                 tightness_factors: Optional[Dict[str, float]] = None,
                 career_years: float = CAREER_YEARS,
                 hours_per_year: float = HOURS_PER_WORKER_YEAR) -> None:
        self.money_per_labour_hour = money_per_labour_hour
        self.subsistence_hours_per_hour = subsistence_hours_per_hour
        self.hours_per_year = hours_per_year
        self.tightness_factors = tightness_factors if tightness_factors is not None else {}
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
        wage = (self.money_per_labour_hour * self.premium(trade)
                * self.tightness_factors.get(trade, 1.0))
        # Anyone can fall back to unskilled work, so nothing pays below the floor.
        return max(self.floor_per_hour, wage)

    def annual_wage(self, trade: str) -> float:
        return self.wage_per_hour(trade) * self.hours_per_year

    def wages_per_hour(self) -> Dict[str, float]:
        return {trade: self.wage_per_hour(trade) for trade in sorted(self._premium)}

    def step(self, hours_required_by_trade: Mapping[str, float],
             hours_by_trade: Mapping[str, float]) -> None:
        """Advance every trade's tightness factor one year."""
        for trade in sorted(self._premium):
            self.tightness_factors[trade] = adjusted_tightness_factor(
                self.tightness_factors.get(trade, 1.0),
                hours_required_by_trade.get(trade, 0.0),
                hours_by_trade.get(trade, 0.0))

    def document(self) -> Dict[str, Any]:
        """The wage table in the shape the price solver reads, with the money
        value of a labour hour that turns its labour-hour prices into money."""
        return {"wage_rates_denarii_per_hour":
                {trade: {"rate": wage} for trade, wage in self.wages_per_hour().items()},
                "money_per_labour_hour": self.money_per_labour_hour}

    def ratio_document(self) -> Dict[str, Any]:
        """The same shape in numeraire units, before any floor or tightness:
        the training premium alone, with one labour hour worth one unit."""
        return {"wage_rates_denarii_per_hour":
                {trade: {"rate": premium} for trade, premium in sorted(self._premium.items())},
                "money_per_labour_hour": 1.0}

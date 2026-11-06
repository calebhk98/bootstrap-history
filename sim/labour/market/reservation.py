"""What an hour of work must pay: the outside option per hour plus the priced risk of the trade."""
from typing import Optional

from .records import YearInputs


def reservation_wage_per_hour(subsistence_per_year: float, hours_per_year: float, risk: float,
                              value_of_life_years: float) -> float:
    """Per hour: the outside option (subsistence over the year's hours) plus the priced yearly risk of death."""
    if hours_per_year <= 0.0:
        raise ValueError("hours_per_year must be positive")
    return subsistence_per_year / hours_per_year * (1.0 + max(0.0, risk) * value_of_life_years)


def reservation_wage(inputs: YearInputs, area: str, risk: float) -> Optional[float]:
    """What an hour must pay: the outside option per hour plus the priced risk of the trade; None where the area has
    no stated outside option."""
    subsistence = inputs.subsistence_per_worker_year.get(area)
    if subsistence is None:
        return None
    return reservation_wage_per_hour(subsistence, max(inputs.hours_per_worker_year, 1e-12), risk,
                                     inputs.value_of_life_years_of_income)

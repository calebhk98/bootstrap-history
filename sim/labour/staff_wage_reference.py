"""The wage an affordability budget is divided by to give a headcount."""
import statistics


def blended_annual_wage(annual_wages):
    """The typical annual wage across trades: the median, so that one trade with a handful of hands, whose wage this
    year is far above the rest while it is scarce, does not turn the whole budget into no hires. None for no wages."""
    wages = list(annual_wages)
    return statistics.median(wages) if wages else None

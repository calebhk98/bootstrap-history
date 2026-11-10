"""What the year's kernels read about the world, as arrays on the state's numbering (`income_kernel.YearRates`)."""
import numpy as np

from .income_kernel import YearRates
from .market_state import MarketState
from .records import YearInputs


def rates_of(state: MarketState, inputs: YearInputs) -> YearRates:
    """The year's subsistence by area, risk and training years by trade, and the scalar rules."""
    ids = state.ids
    subsistence = np.full(len(ids.areas), np.nan)
    for area, value in inputs.subsistence_per_worker_year.items():
        if ids.areas.find(area) is not None:
            subsistence[ids.areas.number(area)] = value
    specs = [inputs.trades.get(name) for name in ids.trades.names]
    return YearRates(inputs.hours_per_worker_year, inputs.discount_rate, inputs.career_years, inputs.value_of_life_years_of_income, subsistence,
                     np.array([spec.fatality_risk_per_year if spec else 0.0 for spec in specs]),
                     np.array([spec.training_years if spec else 0.0 for spec in specs]))

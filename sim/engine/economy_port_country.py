"""What one partner country's part of the agent economy answers, in coin (part of the port).

The wage, the output, the cost of living and the prices are read from the country's own tiles in the one
economy (sim/economy/country_figures.py); a figure it has no record of is None and the caller keeps its
labelled estimate."""
from typing import Dict, Optional

from sim.economy.api import country_figures, trade_premium


class CountryAnswers:
    """The questions foreign governments, strata and firms ask about their country, answered from its tiles."""

    def __init__(self, economy, country: str) -> None:
        self._economy = economy
        self._country = country
        setup = economy.setup
        self._coin = setup.coin_per_unit
        self._hours = setup.working_hours_per_year
        self._wages = {trade: wage * self._coin
                       for trade, wage in country_figures.wages_per_hour(economy, country).items()}

    def has_labour_market(self) -> bool:
        return bool(self._wages)

    def pay_per_person_year(self, trade: str) -> Optional[float]:
        """What a person-year of a trade pays in the country's labour markets; a trade nobody hired is paid what
        its training adds to the unskilled wage, as at home. None while the country's markets have no wage."""
        setup = self._economy.setup
        if trade in self._wages:
            return self._wages[trade] * self._hours
        unskilled = self._wages.get(setup.unskilled_trade)
        if unskilled is None:
            return None
        return unskilled * (1.0 + trade_premium(setup, trade)) * self._hours

    def society_output(self) -> Optional[float]:
        output = country_figures.output_value(self._economy, self._country)
        return None if output is None else output * self._coin

    def need_floor_costs_per_person_year(self) -> Dict[str, float]:
        return {need: cost * self._coin for need, cost in
                country_figures.need_floor_costs_per_person_year(self._economy, self._country).items()}

    def population(self) -> float:
        return country_figures.population(self._economy, self._country)

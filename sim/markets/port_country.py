"""What one partner country's part of the agent economy answers, in coin (part of the port).

The wage, the output, the cost of living and the prices are read from the country's own tiles in the one
economy (sim/economy/country_figures.py); a figure it has no record of is None and the caller keeps its
labelled estimate."""
import math
from typing import Dict, Optional

from .unit_mass import tonnes_per_unit
from sim.economy.api import (carried_book, cohort_land_rents, country_figures, land_rent_at_tile, coin_per_unit,
                             country_trade_wage, working_hours_per_year)


def trade_book_in_coin(economy, country: str) -> Dict[str, Dict[str, float]]:
    """What crossed the country's border last year by good: tonnes each way, and money each way in coin (imports at the price
    where they landed, exports at the price where they left)."""
    coin = coin_per_unit(economy)
    return {good: {key: value * coin if key.endswith("_value") else value for key, value in entry.items()}
            for good, entry in country_figures.trade_book(economy, country).items()}


class CountryAnswers:
    """The questions foreign governments, strata and firms ask about their country, answered from its tiles."""

    def __init__(self, economy, country: str) -> None:
        self._economy = economy
        self._country = country
        self._coin = coin_per_unit(economy)
        self._hours = working_hours_per_year(economy)

    def pay_per_person_year(self, trade: str) -> float:
        """What a person-year of a trade pays in the country's labour markets; a trade nobody hired is at the core's area wages, and one with none by the
        one rule (sim/economy/trade_wages.py) on the country's unskilled wage."""
        return country_trade_wage(self._economy, trade, self._country) * self._coin * self._hours

    def society_output(self) -> Optional[float]:
        output = country_figures.output_value(self._economy, self._country)
        return None if output is None else output * self._coin

    def need_floor_costs_per_person_year(self) -> Dict[str, float]:
        return {need: cost * self._coin for need, cost in
                country_figures.need_floor_costs_per_person_year(self._economy, self._country).items()}

    def population(self) -> float:
        return country_figures.population(self._economy, self._country)

    def price_per_tonne(self, material: str) -> Optional[float]:
        """Money for a tonne of a material at the price its market areas touching the country quote; None when
        none of them trades it."""
        price = country_figures.prices(self._economy, self._country).get(material)
        per_unit = tonnes_per_unit(material)
        return None if price is None or per_unit is None else price * self._coin / per_unit

    def price_per_unit(self, material: str) -> Optional[float]:
        """Money for one unit of a material at the price its market areas touching the country quote; None when none
        of them trades it."""
        price = country_figures.prices(self._economy, self._country).get(material)
        return None if price is None else price * self._coin

    def coin_regime(self) -> str:
        """The standard of the money the one economy uses."""
        return country_figures.currency(self._economy).regime

    def coin_stock_value(self) -> Optional[float]:
        """Money's worth of the backing metal in the money held on the country's tiles, at the country's price of
        that metal; None for fiat money (no metal) and while the metal has no price."""
        spec = country_figures.currency(self._economy)
        price = country_figures.prices(self._economy, self._country).get(spec.backing_good) if spec.backing_good else None
        if price is None:
            return None
        held = country_figures.money_held(self._economy, self._country)
        return held * spec.backing_per_unit * price * self._coin

    def trade_book(self) -> Dict[str, Dict[str, float]]:
        """The goods that crossed the country's border last year: tonnes and money each way, by good (imports at the
        price where they landed, exports at the price where they left)."""
        return trade_book_in_coin(self._economy, self._country)

    def trade_value(self, direction: str) -> float:
        """Money's worth of the goods imported ("in") or exported ("out") last year: what the merchants carried across the
        border."""
        return carried_book.trade_value(self.trade_book(), direction)

    def people_of_trade(self, trade: str) -> float:
        """Working people of a trade in the labour markets of the country's tiles (nobody for a trade none practise)."""
        return country_figures.people_by_trade(self._economy, self._country).get(trade, 0.0)

    def idle_hours_by_trade(self) -> Dict[str, tuple]:
        """(hours offered and not hired, hours offered) of each trade in the labour markets of the country's tiles last year."""
        return country_figures.idle_hours_by_trade(self._economy, self._country)

    def working_people(self) -> Optional[float]:
        """Every working person in the labour markets of the country's tiles, whatever the trade: the hands unskilled
        labour can draw on (the working age at home). None where the country's labour markets hold nobody."""
        people = math.fsum(country_figures.people_by_trade(self._economy, self._country).values())
        return people if people > 0.0 else None

    def land_rent_at(self, tile: Optional[str]) -> Optional[float]:
        """Rent per hectare-year in coin on a tile of the country, the mean of the country's let land where none was let
        on it (or the tile is not the country's); None where the country let no land."""
        economy = self._economy
        own_tiles = country_figures.country_tiles(economy, self._country)
        rent = land_rent_at_tile(economy, tile if tile in own_tiles else None, self._country)
        return rent * self._coin if rent > 0.0 else None

    def land_rent_curve(self, tiles=None):
        """(people, rent received in coin) of the country's household cohorts, poorest first: the rent paid on its
        tiles (only `tiles` of them when given) goes to the cohorts that own the land."""
        tiles = None if tiles is None else set(tiles)
        return [(people, rent * self._coin)
                for people, rent in cohort_land_rents(self._economy, tiles, self._country)]

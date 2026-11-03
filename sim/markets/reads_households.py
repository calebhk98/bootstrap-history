"""What the agent economy answers about its households, land rents, partner countries and the volumes it traded. Part of the
port. Money is counted in coin here, the engine's unit; quantities in tonnes."""
from sim.economy import api as economy_api

from .port_country import trade_book_in_coin


class HouseholdReads:

    def __init__(self, agent):
        self._agent = agent

    def cohort_incomes(self):
        """(people, yearly income in coin) of the household cohorts, poorest per head first."""
        economy = self._agent.economy()
        coin = economy_api.coin_per_unit(economy)
        return [(people, income * coin) for people, income in economy_api.cohort_incomes(economy)]

    def cohort_land_rents(self, tiles=None):
        """(people, rent received last year in coin) in the order of `cohort_incomes`; only rent paid on `tiles` when given."""
        economy = self._agent.economy()
        coin = economy_api.coin_per_unit(economy)
        return [(people, rent * coin) for people, rent in economy_api.cohort_land_rents(economy, tiles)]

    def country(self, country):
        """What the economy answers for a partner country in it (`CountryAnswers`), or None when the country is
        the home country or not in this economy (a country in it always answers: the one wage rule prices a trade its markets have not paid)."""
        economy = self._agent.economy()
        if country == economy_api.home_country(economy) or country not in economy_api.economy_countries(economy):
            return None
        from .port_country import CountryAnswers
        return CountryAnswers(economy, country)

    def trade_book(self, country):
        """What crossed the country's border last year, by good ({good: {"in_tonnes", "in_value", "out_tonnes", "out_value"}}),
        the values in coin like every other money figure here."""
        return trade_book_in_coin(self._agent.economy(), country)

    def land_rent_per_hectare(self):
        """Mean rent per hectare-year the land market let land at last year, in coin."""
        economy = self._agent.economy()
        return economy_api.land_rent_per_hectare(economy) * economy_api.coin_per_unit(economy)

    def land_rent_at_tile(self, tile):
        """Rent per hectare-year on one tile in coin (the mean where none was let there)."""
        economy = self._agent.economy()
        return economy_api.land_rent_at_tile(economy, tile) * economy_api.coin_per_unit(economy)

    def land_rent_paid_by_tile(self):
        """Rent producers paid on each tile where land was let last year, in coin."""
        economy = self._agent.economy()
        coin = economy_api.coin_per_unit(economy)
        return {tile: rent * coin for tile, rent in economy_api.land_rent_paid_by_tile(economy).items()}

    def need_floor_costs_per_person_year(self, country=None):
        """What a person's floor of each need costs a year at the prices on the home tiles (the mean over the
        people there), in coin; empty before any tile holds people."""
        economy = self._agent.economy()
        figures = self._agent.figures
        scope = economy_api.country_figures.home_when_shared(economy, country)
        if economy is not figures.floor_costs_of:
            figures.floor_costs, figures.floor_costs_of = {}, economy
        if scope not in figures.floor_costs:
            costs = economy_api.country_figures.need_floor_costs_per_person_year(economy, scope)
            figures.floor_costs[scope] = {need: cost * economy_api.coin_per_unit(economy) for need, cost in costs.items()}
        return dict(figures.floor_costs[scope])

    def need_floor_costs_at_tile(self, tile):
        """What a person's floor of each need costs a year at the prices on one tile, in coin."""
        economy = self._agent.economy()
        costs = economy_api.country_figures.tile_need_floor_costs(economy, tile)
        return {need: cost * economy_api.coin_per_unit(economy) for need, cost in costs.items()}

    def idle_hours_by_trade(self):
        """(hours offered and not hired, hours offered) of each trade in the home labour markets last year."""
        return economy_api.idle_hours_by_trade(self._agent.economy())

    def fugitive_share_by_tile(self):
        """{tile: share of the people who belonged to it that are away having fled the state's take}; empty before the economy opens."""
        return economy_api.fugitive_share_by_tile(self._agent.economy()) if self._agent.opened() else {}

    def volume_baseline(self, country=None):
        """{good: units cleared in the first year the country's markets cleared any}."""
        economy = self._agent.economy()
        baseline = self._agent.stored.get("volume_baseline", {})
        return dict(baseline.get(country or economy_api.home_country(economy), {}))

    def traded_volumes(self, country=None):
        return economy_api.country_traded_volumes(self._agent.economy(), country)

    def opening_basket(self, country=None):
        """(units a year of each good in the country's opening basket, opening price of each in labour hours)."""
        economy = self._agent.economy()
        return economy_api.country_opening_basket(economy, country), economy_api.opening_prices_in_hours(economy)

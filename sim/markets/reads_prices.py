"""What the agent economy answers about prices, wages, the rate and its markets' books. Part of the port.

Money is counted in coin here, the engine's unit; quantities in tonnes. Everything is read through `sim.economy.api` and
kept in the agent's `YearFigures` until the economy's state changes."""
from sim.economy import api as economy_api
from sim.world.material_units import tonnes_per_unit

from .trade_wage import trade_wage_at, unpriced_trade_wage


class PriceReads:

    def __init__(self, agent, world):
        self._agent = agent
        self._world = world

    def answers(self, country=None):
        """(prices by good, hours-weighted wage per hour by trade, rate), for this year; built once a year. A good
        whose markets have not cleared lately shows what it costs to make at today's prices and wages, or
        its last price when nothing makes it; `stale_goods()` names those. For a partner `country` that is part
        of the economy, those of its own markets; any other country is answered as the home country."""
        agent = self._agent
        figures = agent.figures
        if country is not None and country != self._world.scenario.civ.get("id"):
            home = self.answers()
            economy = agent.economy()
            if country not in economy_api.economy_countries(economy):
                return home
            if country not in figures.country_answers:
                coin = economy_api.coin_per_unit(economy)
                prices, _stale = economy_api.shown_prices_of(economy, country)
                wages = economy_api.wages_by_trade_weighted(economy, country)
                figures.country_answers[country] = ({good: price * coin for good, price in prices.items()},
                                                    {trade: wage * coin for trade, wage in wages.items()}, home[2])
            return figures.country_answers[country]
        if figures.answers is None or not agent.current():
            economy = agent.economy()
            wages = economy_api.wages_by_trade_weighted(economy)
            coin = economy_api.coin_per_unit(economy)
            prices, figures.stale = economy_api.shown_prices_of(economy)
            figures.answers = ({good: price * coin for good, price in prices.items()},
                               {trade: wage * coin for trade, wage in wages.items()},
                               economy_api.interest_rate(economy))
        return figures.answers

    def price_kind(self, good):
        """What the shown price of a good is (economy_api.shown_price_kinds_of): smoothed_trade, a quote named by what it
        is, or an estimate; None for a good the economy shows no price for. Built once a year."""
        answers = self.answers()
        figures = self._agent.figures
        if figures.kinds is None or figures.kinds[0] is not answers:
            figures.kinds = (answers, economy_api.shown_price_kinds_of(self._agent.economy()))
        return figures.kinds[1].get(good)

    def stale_goods(self):
        """Goods whose shown price is not a market's: not cleared within notional.RECENT_TRADE_YEARS."""
        self.answers()
        return set(self._agent.figures.stale)

    def prices_at(self, tile):
        """{good: money per unit} on the tile in coin; the same dict while the year's answers stand."""
        answers = self.answers()
        tile = self._agent.tile_in_economy(tile)
        figures = self._agent.figures
        held = figures.tile_prices
        if held is None or held[0] is not answers:
            held = figures.tile_prices = (answers, {})
        if tile not in held[1]:
            economy = self._agent.economy()
            coin = economy_api.coin_per_unit(economy)
            prices, _stale = economy_api.prices_at(economy, tile)
            held[1][tile] = {good: price * coin for good, price in prices.items()}
        return held[1][tile]

    def offered_tonnes(self, material, tile):
        """Tonnes the sellers of a material in the tile's market area held at the last clearing; None when the area
        has no book for it."""
        per_unit = tonnes_per_unit(material)
        economy = self._agent.economy()
        if not per_unit or per_unit <= 0.0 or material not in economy.area_map.goods():
            return None
        units = economy_api.offered_units(economy, material, self._agent.tile_in_economy(tile))
        return None if units is None else units * per_unit

    def rate(self):
        return self.answers()[2]

    def unskilled_wage_per_hour(self):
        """The home labour markets' wage for an hour of the trade anyone can take up, in coin."""
        wages = self.answers()[1]
        return wages.get(economy_api.unskilled_trade(self._agent.economy()))

    def wage_per_hour_at(self, trade, tile):
        """The wage per hour, in coin, a bid for the trade on `tile` is funded at (trade_wage.py): the wage of the tile's own
        labour area, else the unpriced-trade wage; None when neither exists."""
        economy = self._agent.economy()
        wage = trade_wage_at(economy, trade, self._agent.tile_in_economy(tile))
        return None if wage is None else wage * economy_api.coin_per_unit(economy)

    def hours_offered_at(self, trade, tile):
        """Hours of the trade the households of `tile`'s labour area offered at the last clearing; None before one."""
        economy = self._agent.economy()
        return economy_api.hours_offered_in_area_of(economy, trade, self._agent.tile_in_economy(tile))

    def wage_per_hour(self, trade, country=None):
        """The country figure: the trade's hours-weighted wage over the country's labour markets; a trade no market has priced (soldiers, scribes) has the wage the staff
        bids use for it (trade_wage.py), so every wage stands on the same rule."""
        wages = self.answers(country)[1]
        if trade in wages:
            return wages[trade]
        economy = self._agent.economy()
        unpriced = unpriced_trade_wage(economy, trade)
        return None if unpriced is None else unpriced * economy_api.coin_per_unit(economy)

    def credit_room(self, borrower_id):
        """What the credit market will still advance one borrower, in coin; None before lenders have met."""
        self.answers()
        economy = self._agent.economy()
        room = economy_api.credit_room(economy, borrower_id)
        return None if room is None else room * economy_api.coin_per_unit(economy)

    def trades_good(self, material):
        """Whether the economy has a market for the material."""
        return material in self._agent.economy().area_map.goods()

    def market_record(self, material):
        """Tonnes the material's markets sold, left unsold and left unmet last year."""
        per_unit = tonnes_per_unit(material)
        return {name: quantity * per_unit
                for name, quantity in economy_api.market_record(self._agent.economy(), material).items()}

    def price_response(self, material, landed_tonnes, taken_tonnes, tile=None):
        """Factor on a material's price once more tonnes land in its market or are taken out, from the book the
        market last cleared: at the port when no tile is named (the price the economy shows nationally), else on the
        tile's own area. None when the market has none."""
        per_unit = tonnes_per_unit(material)
        economy = self._agent.economy()
        if not per_unit or per_unit <= 0.0 or material not in economy.area_map.goods():
            return None
        return economy_api.price_response(economy, material, landed_tonnes / per_unit, taken_tonnes / per_unit,
                                          tile=None if tile is None else self._agent.tile_in_economy(tile))

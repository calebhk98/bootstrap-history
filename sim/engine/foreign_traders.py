"""What merchants add to freight on a foreign route and how fast they respond.

The route's freight prices the carrier; the cargo's own cost is here: the
merchants' margin, the expected loss of cargo on the legs, and interest at the
market rate on the money tied up while goods travel and sit in inventory. The
yearly flow moves part of the way to the arbitrage volume (`sim/world/trader_response.py`)
and is limited by the money merchants can finance.
"""
from sim.constants import declare
from sim.world import freight_cost, trader_response

MERCHANT_MARGIN_SHARE = declare(
    "MERCHANT_MARGIN_SHARE", 0.03, kind="temporary_heuristic",
    unit="share of the price paid at the origin", source=None, confidence="D",
    why="What a merchant keeps for his own labour and for the trades that fail, over freight, "
        "loss and interest; a merchant labour market and a failure rate would derive it.")
MERCHANT_INVENTORY_YEARS = declare(
    "MERCHANT_INVENTORY_YEARS", 0.25, kind="temporary_heuristic",
    unit="years goods wait unsold, on top of the voyage", source=None, confidence="D",
    why="Cargo is held at the origin before loading and at the destination until sold; a "
        "stock-and-sales model of the trading ports would replace the fixed wait.")
TRADER_ADJUSTMENT_SHARE = declare(
    "TRADER_ADJUSTMENT_SHARE", 0.2, kind="temporary_heuristic",
    unit="share of the gap to the arbitrage volume closed in a year", source=None, confidence="D",
    why="Merchants find suppliers, buyers and credit one season at a time, so a flow builds over "
        "years; contracts and information costs would derive the speed.")
MERCHANT_CAPITAL_SHARE_OF_COIN_STOCK = declare(
    "MERCHANT_CAPITAL_SHARE_OF_COIN_STOCK", 0.05, kind="temporary_heuristic",
    unit="share of the home coin stock", source=None, confidence="D",
    why="Money merchants can put into goods in transit and in inventory; a capital market that "
        "lends to merchants (sim/world/capital_market.py) would replace the share.")
DAYS_PER_YEAR = 365.0


class ForeignTradersMixin:

    def _trader_cycle_years(self, route):
        """Years money is tied up in a cargo: the voyage and the wait."""
        travel_days = 0.0 if route is None else sum(leg.travel_days for leg in route.legs)
        return travel_days / DAYS_PER_YEAR + MERCHANT_INVENTORY_YEARS

    @staticmethod
    def _route_cargo_loss_share(route):
        """Share of cargo lost on the route: the hull loss rate over its sea legs."""
        if route is None:
            return 0.0
        sailed_km = sum(leg.distance_km for leg in route.legs if leg.mode == "sea")
        return min(0.9, freight_cost.HULL_LOSS_PER_THOUSAND_KM * sailed_km / 1000.0)

    def _trader_cost_share(self, route):
        return trader_response.cost_share_of_price(
            MERCHANT_MARGIN_SHARE, self._route_cargo_loss_share(route), self.market_rate(),
            self._trader_cycle_years(route))

    def merchant_capital_left(self, civilization_id):
        """Home money merchants can still tie up in goods this year."""
        coin = self.civ["coin_standard"]
        coin_price = self._material_prices().get(coin["material"], 0.0)
        capital = (MERCHANT_CAPITAL_SHARE_OF_COIN_STOCK * self.home_coin_stock_units()
                   * coin["kg_per_unit"] * coin_price)
        ledger = self._foreign_ledger(civilization_id)
        used = ledger["merchant_capital_used"] if ledger["lift_year"] == self.state.scenario.year else 0.0
        return max(0.0, capital - used)

    def trader_terms(self, civilization_id, facts, home_price, foreign_price):
        """`TraderTerms` for a route this year; capital limits in tonnes each way at these prices."""
        route = facts["route"]
        cycle = self._trader_cycle_years(route)
        left = self.merchant_capital_left(civilization_id)
        return trader_response.TraderTerms(
            self._trader_cost_share(route), TRADER_ADJUSTMENT_SHARE,
            capital_tonnes_in=left / (foreign_price * cycle) if foreign_price > 0.0 else 0.0,
            capital_tonnes_out=left / (home_price * cycle) if home_price > 0.0 else 0.0)

    def _flow_capital_tied(self, civilization_id, commodity, flow, home_entry, foreign_outcome, facts):
        """Home money merchants tied up in a flow for a cycle, at the exporter's price."""
        value = self._flow_value(civilization_id, commodity, flow, home_entry, foreign_outcome, facts)
        return 0.0 if value is None else value * self._trader_cycle_years(facts["route"])

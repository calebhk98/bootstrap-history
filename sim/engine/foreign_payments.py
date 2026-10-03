"""What foreign trade is paid with and carried by.

Per partner the state keeps a ledger: the value of goods in and out, the coin units that moved
(negative for the home side when it paid out), and the fleet's yearly lift on the route. Goods cross
in coin metal (`sim/world/balance_of_payments.py`): a persistent deficit drains the home stock and
lowers the home price level in traded prices, which makes imports dearer and exports cheaper. A route
lifts only what its carriers can: the fleet grows from what trade could not be carried, up to what
yards can build, and its capital is paid for through the freight rate (`foreign_routes.py`).
"""
import functools

from sim.constants import declare
from sim.world import balance_of_payments
from sim.geography.api import freight_cost, sea_freight
from sim.labour.wages import HOURS_PER_WORKER_YEAR

from .data import load_civ
from sim.labour.wage_provider import people_fed_per_worker

OPENING_CARRIERS_PER_ROUTE = declare(
    "OPENING_CARRIERS_PER_ROUTE", 10.0, kind="temporary_heuristic",
    unit="hull-equivalents on a route at the start", source=None, confidence="D",
    why="Merchants already ply a route when the game opens, so lift is not zero; the number is an "
        "initial condition not yet derived from the route's known traffic.")
YARD_GROWTH_SHARE_PER_YEAR = declare(
    "YARD_GROWTH_SHARE_PER_YEAR", 0.1, kind="temporary_heuristic",
    unit="share of a route's lift added per year at most", source=None, confidence="D",
    why="How fast shipwrights and breeders can add carriers; stands in for yards, timber and "
        "crews, which are not modelled.")


def _lift_years_per_tonne(inputs, working_days, days_on_leg):
    """Carrier-years a leg uses to move a tonne one way: a round trip, empty back."""
    return 2.0 * days_on_leg / (inputs.cargo_tonnes * working_days)


@functools.lru_cache(maxsize=None)
def _partner_opening_units(civilization_id):
    from .data import starting_schedule
    civilization = load_civ(civilization_id)
    workers = float(civilization.get("population") or 0.0) / people_fed_per_worker()
    return balance_of_payments.opening_stock_units(
        workers, starting_schedule(civilization_id).money_per_labour_hour * HOURS_PER_WORKER_YEAR)


class ForeignPaymentsMixin:

    LEDGER_FIELDS = ("goods_in_value", "goods_out_value", "home_coin_units", "partner_coin_units",
                     "lift_tonnes_per_year", "lift_used_in", "lift_used_out", "lift_unmet",
                     "lift_year", "fleet_capital", "merchant_capital_used", "merchant_retained")

    def _foreign_ledger(self, civilization_id, create=False):
        """The partner's ledger; an empty one when nothing has been recorded and `create` is false."""
        ledgers = self.state.economy.foreign_ledger
        if civilization_id in ledgers:
            return ledgers[civilization_id]
        blank = {field: 0.0 for field in self.LEDGER_FIELDS}
        if not create:
            return blank
        ledgers[civilization_id] = blank
        return blank

    # ---- coin ---------------------------------------------------------------

    def _opening_coin_units(self, wage_per_year):
        workers = self._opening_population() / people_fed_per_worker()
        return balance_of_payments.opening_stock_units(workers, wage_per_year)

    def _home_opening_coin_units(self):
        """Coin the society opened with, at the opening's money (not today's price level)."""
        opening = self.__dict__.get("_opening_coin_value")
        if opening is None:
            opening = self._opening_coin_value = self._opening_coin_units(
                self._opening_wage_schedule().opening_money_per_labour_hour * HOURS_PER_WORKER_YEAR)
        return opening

    def home_coin_stock_units(self):
        """Coin this society holds: its opening stock plus what trade has brought in."""
        return self._home_opening_coin_units() + sum(
            ledger["home_coin_units"] for ledger in self.state.economy.foreign_ledger.values())

    def home_price_level(self):
        """Price level of this society against its opening one: its coin stock against the opening's, the
        level of every good and wage in the home money, traded or not."""
        held = self.__dict__.get("_price_level_held")
        if held is not None:
            return held
        opening = self.__dict__.get("_opening_coin_value") or self._home_opening_coin_units()
        stock = opening + sum(ledger["home_coin_units"] for ledger in self.state.economy.foreign_ledger.values())
        return balance_of_payments.price_level(stock, opening)

    def _partner_coin_opening_units(self, civilization_id):
        return _partner_opening_units(civilization_id)

    def partner_price_level(self, civilization_id):
        ledger = self._foreign_ledger(civilization_id)
        opening = self._partner_coin_opening_units(civilization_id)
        return balance_of_payments.price_level(opening + ledger["partner_coin_units"], opening)

    def foreign_balance_of_payments(self, civilization_id):
        """{goods in, goods out, net coin paid out by this society, home coin stock, price levels, the
        fleet's yearly lift}, money in home units, cumulative."""
        ledger = self._foreign_ledger(civilization_id)
        return {"goods_in_value": ledger["goods_in_value"], "goods_out_value": ledger["goods_out_value"],
                "coin_paid_out_units": -ledger["home_coin_units"],
                "home_coin_stock_units": self.home_coin_stock_units(),
                "home_price_level": self.home_price_level(),
                "partner_price_level": self.partner_price_level(civilization_id),
                "fleet_lift_tonnes_per_year": ledger["lift_tonnes_per_year"]}

    TRADE_YEARS_KEPT = 3

    def _note_trade_value(self, flow_tonnes, value):
        """Add a flow's value to this year's imports or exports; only the last few years are kept."""
        by_year = self.state.economy.foreign_trade_by_year
        year = self.state.scenario.year
        entry = by_year.setdefault(str(year), {"in": 0.0, "out": 0.0})
        entry["in" if flow_tonnes > 0.0 else "out"] += value
        for old in [key for key in by_year if int(key) <= year - self.TRADE_YEARS_KEPT]:
            del by_year[old]

    def _settle_flow(self, civilization_id, flow_tonnes, value, home_money_per_partner_coin):
        """Pay for one commodity's flow in coin: this society pays for imports and is paid for
        exports, never more than the payer holds. `value` is in home money."""
        ledger = self._foreign_ledger(civilization_id, create=True)
        self._note_trade_value(flow_tonnes, value)
        if flow_tonnes > 0.0:
            ledger["goods_in_value"] += value
            paid = balance_of_payments.coin_paid(value, self.home_coin_stock_units())
            ledger["home_coin_units"] -= paid
            ledger["partner_coin_units"] += paid / home_money_per_partner_coin
        elif flow_tonnes < 0.0:
            ledger["goods_out_value"] += value
            partner_units = value / home_money_per_partner_coin
            partner_stock = (self._partner_coin_opening_units(civilization_id)
                             + ledger["partner_coin_units"])
            paid_units = balance_of_payments.coin_paid(partner_units, partner_stock)
            ledger["partner_coin_units"] -= paid_units
            ledger["home_coin_units"] += paid_units * home_money_per_partner_coin

    # ---- carriers -----------------------------------------------------------

    def _route_lift_years_per_tonne(self, route):
        """Carrier-years of lift one tonne a year over the whole route needs; None for no route."""
        if route is None or not route.legs:
            return None
        models = self._carrier_models()
        total = 0.0
        for leg in route.legs:
            inputs, _prices, working_days, _loss = models[leg.mode]
            total += _lift_years_per_tonne(inputs, working_days, leg.travel_days)
        return total

    def _route_capital_per_lift_tonne(self, route):
        """Money of carriers one tonne a year of lift over the route needs."""
        models = self._carrier_models()
        total = 0.0
        for leg in route.legs:
            inputs, prices, working_days, _loss = models[leg.mode]
            total += _lift_years_per_tonne(inputs, working_days, leg.travel_days) * (
                prices.vehicle + prices.animals)
        return total

    def foreign_lift_capacity_tonnes(self, civilization_id, route):
        """Tonnes a year the route's carriers lift in each direction; infinite for a route of no legs."""
        years_per_tonne = self._route_lift_years_per_tonne(route)
        if years_per_tonne is None:
            return float("inf")
        ledger = self._foreign_ledger(civilization_id)
        if ledger["lift_tonnes_per_year"] > 0.0:
            return ledger["lift_tonnes_per_year"]
        return OPENING_CARRIERS_PER_ROUTE / years_per_tonne

    def foreign_lift_left_tonnes(self, civilization_id, route):
        """(into home, out of home) tonnes of lift still free this year."""
        capacity = self.foreign_lift_capacity_tonnes(civilization_id, route)
        ledger = self._foreign_ledger(civilization_id)
        year = self.state.scenario.year
        if ledger["lift_year"] != year:
            return capacity, capacity
        return (max(0.0, capacity - ledger["lift_used_in"]),
                max(0.0, capacity - ledger["lift_used_out"]))

    def _record_lift(self, civilization_id, route, flow_tonnes, unmet_tonnes, capital_tied=0.0):
        ledger = self._foreign_ledger(civilization_id, create=True)
        year = self.state.scenario.year
        if ledger["lift_year"] != year:
            ledger["lift_year"] = year
            ledger["lift_used_in"] = ledger["lift_used_out"] = ledger["lift_unmet"] = 0.0
            ledger["merchant_capital_used"] = 0.0
        if ledger["lift_tonnes_per_year"] <= 0.0:
            ledger["lift_tonnes_per_year"] = self.foreign_lift_capacity_tonnes(civilization_id, route)
        ledger["lift_used_in" if flow_tonnes > 0.0 else "lift_used_out"] += abs(flow_tonnes)
        ledger["lift_unmet"] += unmet_tonnes
        ledger["merchant_capital_used"] += capital_tied

    def foreign_fleet_year_end(self):
        """Grow each route's fleet by what could not be carried this year (within what yards can
        build) and retire the worn share of it."""
        for civilization_id in self.foreign_economies():
            ledger = self.state.economy.foreign_ledger.get(civilization_id)
            if not ledger or ledger["lift_year"] != self.state.scenario.year:
                continue
            route = self._foreign_economy_facts(civilization_id)["route"]
            capacity = self.foreign_lift_capacity_tonnes(civilization_id, route)
            if route is None or capacity == float("inf"):
                continue
            opening = OPENING_CARRIERS_PER_ROUTE / self._route_lift_years_per_tonne(route)
            built = min(ledger["lift_unmet"],
                        max(capacity, opening) * YARD_GROWTH_SHARE_PER_YEAR)
            life = (sea_freight.HULL_SERVICE_LIFE_YEARS if any(leg.mode == "sea" for leg in route.legs)
                    else freight_cost.ANIMAL_WORKING_LIFE_YEARS)
            ledger["fleet_capital"] += built * self._route_capital_per_lift_tonne(route)
            ledger["lift_tonnes_per_year"] = capacity * (1.0 - 1.0 / life) + built
            ledger["lift_unmet"] = 0.0

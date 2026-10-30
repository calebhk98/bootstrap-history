"""What foreign trade is paid with and carried by.

Per partner the module keeps a ledger: the value of goods in and out, the coin units that moved (negative for the home side when
it paid out), and the fleet's yearly lift on the route. Goods cross in coin metal (`sim/world/balance_of_payments.py`): a
persistent deficit drains the home stock and lowers the home price level in traded prices, which makes imports dearer and
exports cheaper. A route lifts only what its carriers can: the fleet grows from what trade could not be carried, up to what
yards can build, and its capital is paid for through the freight rate (`sim/freight/`).

(needs: home_coin_stock, coin_carriage_units, partner_coin_opening, home_unit_price, carrier_models, year)"""
from typing import Any, Dict, Optional, Tuple

from . import rules
from .constants import OPENING_CARRIERS_PER_ROUTE

BOOKS = "books"   # version channel: the partners' books, ledgers and tallies


class Payments:

    def ledger_of(self, civilization_id: str, create: bool = False) -> Dict[str, float]:
        """The partner's ledger; an empty one when nothing has been recorded and `create` is false."""
        ledgers = self.world.ledgers
        if civilization_id in ledgers:
            return ledgers[civilization_id]
        blank = rules.blank_ledger()
        if not create:
            return blank
        ledgers[civilization_id] = blank
        return blank

    def foreign_coin_home_units(self) -> float:
        """Coin units the home society gained (negative: paid out) in trade with every partner."""
        return sum(ledger["home_coin_units"] for ledger in self.world.ledgers.values())

    def foreign_coin_partner_units(self, civilization_id: str) -> float:
        """Coin units a partner gained (negative: paid out) in trade with the home society; none where nothing is booked."""
        return self.ledger_of(civilization_id)["partner_coin_units"]

    def trade_value_in_year(self, year: int) -> Dict[str, float]:
        """{"in": imports, "out": exports} in home money in a year the book still keeps; empty for any other."""
        return self.world.trade_by_year.get(str(year), {})

    def money_per_partner_coin(self, civilization_id: str) -> Optional[float]:
        """Home money one unit of the partner's coin is worth, from its metal at the home price; None when the metal has none."""
        standard = self.partner_civ(civilization_id)["coin_standard"]
        metal_price = self.needs.home_unit_price[standard["material"]]
        return standard["kg_per_unit"] * metal_price if metal_price else None

    def settle_flow(self, civilization_id: str, flow_tonnes: float, value: float, home_money_per_partner_coin: float) -> None:
        """Pay for one commodity's flow in coin: this society pays for imports and is paid for exports, never more than the
        payer holds. `value` is in home money."""
        ledger = self.ledger_of(civilization_id, create=True)
        rules.note_trade_value(self.world.trade_by_year, self.needs.year(), flow_tonnes, value)
        if flow_tonnes > 0.0:
            ledger["goods_in_value"] += value
            paid, received = rules.import_payment(value, self.needs.home_coin_stock(), home_money_per_partner_coin)
            carriage = self.needs.coin_carriage_units(civilization_id, received, home_money_per_partner_coin)
            rules.book_import(ledger, paid, received, carriage, home_money_per_partner_coin)
        elif flow_tonnes < 0.0:
            ledger["goods_out_value"] += value
            partner_stock = self.needs.partner_coin_opening[civilization_id] + ledger["partner_coin_units"]
            paid_units = rules.export_payment(value, partner_stock, home_money_per_partner_coin)
            rules.book_export_paid(ledger, paid_units)
            carriage = self.needs.coin_carriage_units(civilization_id, paid_units, home_money_per_partner_coin)
            rules.book_export(ledger, paid_units, carriage, home_money_per_partner_coin)
        self.bump(BOOKS)

    def apply_settle_flow(self, command: Any) -> None:
        """Pay the partner in its own coin's metal and note the flow; nothing moves while the metal has no home price."""
        per_coin = self.money_per_partner_coin(command.partner)
        if per_coin:
            self.settle_flow(command.partner, command.tonnes, command.value, per_coin)

    def record_lift(self, civilization_id: str, route: Any, flow_tonnes: float, unmet_tonnes: float) -> None:
        ledger = self.ledger_of(civilization_id, create=True)
        rules.reset_lift_year(ledger, self.needs.year())
        if ledger["lift_tonnes_per_year"] <= 0.0:
            ledger["lift_tonnes_per_year"] = self.lift_capacity_tonnes(civilization_id, route)
        rules.book_lift(ledger, flow_tonnes, unmet_tonnes)
        self.bump(BOOKS)

    # ---- carriers -----------------------------------------------------------

    def _route_legs(self, route: Any) -> list:
        models = self.needs.carrier_models()
        return [(models[leg.mode], leg.travel_days) for leg in route.legs]

    def route_lift_years_per_tonne(self, route: Any) -> Optional[float]:
        """Carrier-years of lift one tonne a year over the whole route needs; None for no route."""
        if route is None or not route.legs:
            return None
        return rules.route_lift_years_per_tonne([(model[0], model[2], days) for model, days in self._route_legs(route)])

    def route_capital_per_lift_tonne(self, route: Any) -> float:
        """Money of carriers one tonne a year of lift over the route needs."""
        return rules.route_capital_per_lift_tonne(
            [(model[0], model[1], model[2], days) for model, days in self._route_legs(route)])

    def lift_capacity_tonnes(self, civilization_id: str, route: Any) -> float:
        """Tonnes a year the route's carriers lift in each direction; infinite for a route of no legs."""
        years_per_tonne = self.route_lift_years_per_tonne(route)
        return rules.lift_capacity(years_per_tonne, self.ledger_of(civilization_id)["lift_tonnes_per_year"],
                                   OPENING_CARRIERS_PER_ROUTE)

    def lift_left_tonnes(self, civilization_id: str, route: Any) -> Tuple[float, float]:
        """(into home, out of home) tonnes of lift still free this year."""
        capacity = self.lift_capacity_tonnes(civilization_id, route)
        return rules.lift_left(self.ledger_of(civilization_id), self.needs.year(), capacity)

    def opening_carriers_per_route(self) -> float:
        return OPENING_CARRIERS_PER_ROUTE

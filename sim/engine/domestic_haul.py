"""A domestic haul priced by the one freight function: the carrier's running costs, capital and return
trip, the tolls and dues the geography states for its mode, and, for live animals, their walk.

The return trip follows last year's domestic flow ledger (`sim.geography.flow_ledger`, kept by the
economy as the goods its merchants carried between tiles): the share of capacity the opposite flow
fills is not charged. With no ledger yet, the carrier is taken to return empty.
"""
from sim.geography.api import flow_ledger, freight_cost, provisions, walking_cargo_modes

from .living_stock_yearly import stock_rates

DOMESTIC_CART_MODE = "cart"


class DomesticHaulMixin:

    def _cargo_class(self, material):
        """"living_stock" for stock the living-stock data says walks (animals), else "goods" (seed, cuttings, eggs)."""
        return "living_stock" if stock_rates().get(material, {}).get("walks") else "goods"

    def _domestic_flow_ledger(self):
        """Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}; empty
        until the economy has run a year."""
        record = self.state.economy.agent_economy.get("record") or {}
        return record.get("carried") or {}

    def _domestic_flow_imbalance(self):
        """How one-sided last year's domestic carriage was (1 when nothing is recorded: carts return empty)."""
        return flow_ledger.overall_imbalance(self._domestic_flow_ledger())

    def _domestic_haul_mode(self, cargo):
        """The mode a domestic haul of this class of cargo goes by: the cart for goods, the first mode
        whose cargo walks for living stock."""
        if cargo == "living_stock":
            walking = walking_cargo_modes(self.world_map)
            return walking[0] if walking else DOMESTIC_CART_MODE
        return DOMESTIC_CART_MODE

    def domestic_haul_dues_per_tonne(self, mode=DOMESTIC_CART_MODE):
        """Home money in tolls and dues a haul pays when it changes to the mode (the geography's hours of
        labour at the carriers' wage); the same charge a foreign leg of the mode pays."""
        return self._freight_handling_costs().get(mode, 0.0)

    def domestic_haul_money_per_tonne(self, material, distance_km):
        """Home money to haul a tonne of `material` over `distance_km` of domestic ground: the mode's rate
        (the return trip by last year's flows), over the share of lift left after the carrier's food,
        plus the mode's dues."""
        mode = self._domestic_haul_mode(self._cargo_class(material))
        inputs = self._carrier_models()[mode][0]
        rate = self._freight_mode_costs(self._domestic_flow_imbalance(), (mode,))[mode]
        return freight_cost.leg_money_per_tonne(
            rate, inputs, distance_km, restock_days=provisions.RESTOCK_INTERVAL_DAYS,
            dues_per_tonne=self.domestic_haul_dues_per_tonne(mode))

    def _material_route(self, civilization, material, goods_route):
        """The route a partner's `material` travels: the goods route already found, or for living stock
        the route its own modes make (animals walk overland and are shipped over water)."""
        if self._cargo_class(material) == "goods":
            return goods_route
        return self._foreign_route(civilization, cargo="living_stock")

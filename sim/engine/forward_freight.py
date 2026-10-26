"""One-line forwarders from `Sim` to the freight module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.freight.api import FREIGHT_DRIVER_WAGE_TRADE, FREIGHT_FEED_PRICE_MATERIAL, PayRouteDues


class ForwardFreightMixin:
    FREIGHT_DRIVER_WAGE_TRADE = FREIGHT_DRIVER_WAGE_TRADE
    FREIGHT_FEED_PRICE_MATERIAL = FREIGHT_FEED_PRICE_MATERIAL

    def _foreign_route(self, civilization, imbalance=None, cargo="goods"):
        return self.view("foreign_route")(civilization, imbalance, cargo)

    def _route_freight_per_tonne(self, civilization, imbalance=None):
        return self.view("route_freight_per_tonne")(civilization, imbalance)

    def _freight_mode_costs(self, imbalance=1.0, modes=None, cargo=None):
        return self.view("freight_mode_costs")(imbalance, modes, cargo)

    def _carrier_models(self):
        return self.view("carrier_models")()

    def material_carriage_per_tonne(self, material, price_per_tonne):
        return self.view("material_carriage_per_tonne")(material, price_per_tonne)

    def material_freight_factor(self, material):
        return self.view("material_freight_factor")[material]

    def _trader_margin_share(self, civilization_id, route, price_flexibility=None):
        return self.view("trader_margin_share")(civilization_id, route, price_flexibility)

    def _cargo_lost_share(self, route, material=None, civilization_id=None, destination_demand_tonnes=None):
        return self.view("cargo_lost_share")(route, material, civilization_id, destination_demand_tonnes)

    def _trader_cycle_years(self, route, civilization_id=None, destination_demand_tonnes=None):
        return self.view("trader_cycle_years")(route, civilization_id, destination_demand_tonnes)

    def _agent_cost_per_tonne(self, civilization_id, route):
        return self.view("trader_agent_cost")(civilization_id, route)

    def _domestic_flow_ledger(self):
        return self.view("goods_carried_last_year")()

    def pay_route_dues(self, payer, route, tonnes, limit=None):
        return self.send(PayRouteDues(payer.actor_id, route, tonnes, limit))

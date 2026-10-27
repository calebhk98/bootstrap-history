"""One-line forwarders from `Sim` to the foreign-trade module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.foreign_trade.api import ClosePartnerBooks, NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg, SettleTraderCargo


class ForwardForeignTradeMixin:

    def partner_countries(self):
        return self.view("partners")()

    def partners_in_agent_economy(self):
        return self.view("partners_in_agent_economy")()

    def foreign_economies(self):
        return self.view("foreign_economies")()

    def partner_civ(self, civilization_id):
        return self.view("partner")[civilization_id]["civ"]

    def _foreign_economy_facts(self, civilization_id):
        return self.view("partner_facts")[civilization_id]

    def _commodity_materials(self, commodity):
        return self.view("commodity_materials")[commodity]

    def foreign_supply_tonnes(self, civilization_id, material):
        return self.view("foreign_supply_tonnes")(civilization_id, material)

    def foreign_lift_left_tonnes(self, civilization_id, route):
        return self.view("lift_left_tonnes")(civilization_id, route)

    def partner_price_per_unit(self, partner, material):
        return self.view("partner_price_per_unit")(partner, material)

    def partner_price_response(self, partner, material, tonnes, landing):
        return self.view("partner_price_response")(partner, material, tonnes, landing)

    def actors_carry(self, material, to_partner, partner=None):
        return self.view("actors_carry")(material, to_partner, partner)

    def actor_home_trade(self, material):
        return self.view("actor_home_trade")[material]

    def landed_cost(self, paid, carriage):
        return self.view("landed_cost")(paid, carriage)

    def note_actor_trade(self, partner, material, tonnes, to_partner, landed_cost=0.0):
        return self.send(NoteActorTrade(partner, material, tonnes, to_partner, landed_cost))

    def cargo_legs(self):
        return self.view("cargo_legs")()

    def settle_trader_cargo(self, results):
        return self.send(SettleTraderCargo(results))

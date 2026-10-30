"""What a load bought from a partner costs delivered, and what it costs to carry one out.

(needs: material_route, trader_cost_share, trader_agent_cost, cargo_lost_share, partner_price_level)"""
from typing import Optional, Tuple

from sim.world.material_units import tonnes_per_unit


class Quotes:

    def partner_landed_price(self, civilization_id: str, material: str) -> Optional[float]:
        """Home money per tonne delivered from a partner, or None when it cannot supply it."""
        if civilization_id not in self.partners() or self.partner_refusal(civilization_id, material):
            return None
        facts = self.partner_facts(civilization_id)
        price = facts["prices_in_home_money"].get(material)
        if material not in facts["solved_materials"] or not price:
            return None
        route = self.needs.material_route(self.partner_civ(civilization_id), material, facts["route"])
        if route is None:
            return None
        per_tonne = price / tonnes_per_unit(material) * self.needs.partner_price_level[civilization_id]
        return (per_tonne * (1.0 + self.needs.trader_cost_share(route, material, civilization_id))
                + self.needs.trader_agent_cost(civilization_id, route) + route.cost_per_tonne)

    def partner_carry(self, civilization_id: str, material: str) -> Tuple[float, float]:
        """(money per tonne to carry a load out of a partner by the agents at the two ends and the freight, the share the
        route loses on the way)."""
        facts = self.partner_facts(civilization_id)
        carry_per_tonne = self.needs.trader_agent_cost(civilization_id, facts["route"]) + facts["freight_per_tonne"]
        return carry_per_tonne, self.needs.cargo_lost_share(facts["route"], material, civilization_id)

"""What a load bought from a partner costs delivered, and what it costs to carry one out.

(needs: material_route, trader_cost_share, trader_agent_cost, cargo_lost_share, agent_country)"""
from typing import Optional, Tuple


class Quotes:

    def partner_landed_price(self, civilization_id: str, material: str) -> Optional[float]:
        """Home money per tonne delivered from a partner, at the price its markets in the agent economy quote, or None when it
        cannot supply it."""
        if civilization_id not in self.partners() or self.partner_refusal(civilization_id, material):
            return None
        answers = self.needs.agent_country[civilization_id]
        per_tonne = None if answers is None else answers.price_per_tonne(material)
        if not per_tonne:
            return None
        route = self.needs.material_route(self.partner_civ(civilization_id), material, self.partner_facts(civilization_id)["route"])
        if route is None:
            return None
        return (per_tonne * (1.0 + self.needs.trader_cost_share(route, material, civilization_id))
                + self.needs.trader_agent_cost(civilization_id, route) + route.cost_per_tonne)

    def partner_carry(self, civilization_id: str, material: str) -> Tuple[float, float]:
        """(money per tonne to carry a load out of a partner by the agents at the two ends and the freight, the share the
        route loses on the way)."""
        facts = self.partner_facts(civilization_id)
        carry_per_tonne = self.needs.trader_agent_cost(civilization_id, facts["route"]) + facts["freight_per_tonne"]
        return carry_per_tonne, self.needs.cargo_lost_share(facts["route"], material, civilization_id)

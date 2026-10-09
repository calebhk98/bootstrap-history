"""A concern's running, read from the tenure stock: scrap, unit labour, plant repair and input supply
(Complaint 111). The pure arithmetic is in industry_learning.py.

Delivery time comes from geography alone: the days a haul takes from the nearest tile that makes an input to
the concern's tile. The agent economy carries no lead time per recipe, so nothing is counted twice.
"""
from sim.geography.api import route, usable_modes
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR

from .industry_depth import mastery_worker_years
from .industry_learning import (input_availability, learning_multiplier, learning_value_ratio,
                                repair_hours_by_trade, running_availability, work_hours_by_trade)
from .prices import default_production_entries


class IndustryConcernMixin:

    def tenure_weights(self, node_id):
        """Hours a year each trade works in the concern (running and repairing it); the founding staff when
        the concern's output is not worked out from production data. Worker-years are split by these."""
        baskets = self.concern_baskets_now(node_id)
        if baskets is not None:
            weights = work_hours_by_trade(baskets.labour_hours, repair_hours_by_trade(baskets.plant))
            if sum(weights.values()) > 0.0:
                return weights
        return self.founding_staff_by_trade(node_id)

    def concern_learning_ratio(self, node_id):
        """Share of its stated takings a concern makes, given scrap and unit labour along the experience
        curve, repairs its tenured trades can do and the inputs its suppliers deliver; one without baskets."""
        baskets = self.concern_baskets_now(node_id)
        if baskets is None:
            return 1.0
        held = self.techniques_in_use()
        prices = self._done_memo("concern_prices_held", held, lambda: self._concern_prices_in_hours(held))
        founding = self.founding_worker_years(node_id)
        multiplier = learning_multiplier(self.industry_experience(node_id), founding, mastery_worker_years(founding))
        purchases = {material: quantity * prices.get(material, 0.0) for material, quantity in baskets.purchases.items()}
        purchases_value = sum(purchases.values()) + sum(basket["value"] for basket in baskets.energy_bought.values())
        net = (sum(quantity * prices.get(material, 0.0) for material, quantity in baskets.outputs.items())
               + sum(basket["value"] for basket in baskets.energy_sold.values()) - purchases_value)
        ratio = learning_value_ratio(net, purchases_value, sum(baskets.labour_hours.values()), multiplier)
        repairs = repair_hours_by_trade(baskets.plant)
        ratio *= running_availability(baskets.labour_hours, repairs, self.industry_tenure_by_trade(node_id))
        return ratio * self.concern_input_availability(node_id, purchases)

    def concern_input_availability(self, node_id, purchases_value):
        """Share of the year the concern has its inputs, from the producers the economy runs for each."""
        agent = self.economy.agent
        if agent is None or not purchases_value:
            return 1.0
        year = self.state.scenario.year
        producers = self._done_memo("producers_by_good", year, agent.producers_by_good)
        gate = {key: entry.get("requires_node") for key, entry in default_production_entries().items()}
        depth, lead = {}, {}
        for material in purchases_value:
            found = producers.get(material, ())
            if not found:
                continue
            # a technique that needs no technology is established wherever it is run
            depth[material] = max((self.industry_depth(gate[recipe]) if gate.get(recipe) else 1.0
                                   for _tile, recipe in found), default=0.0)
            days = self._done_memo("input_days", (year, material), lambda: self.days_from_producers(found))
            lead[material] = None if days is None else days / CIVIL_DAYS_PER_YEAR
        return input_availability(purchases_value, depth, lead)

    def days_from_producers(self, found):
        """Fewest days a haul takes to the concern's tile from the nearest tile that makes the input; None
        when no route joins them."""
        base = self.labour.base_tile()
        tiles = sorted({tile for tile, _recipe in found})
        if base in tiles:
            return 0.0
        held = self.labour.held_technologies()
        hauled = route(tiles, [base], usable_modes([held]), self.state.economy.improvements, held_nodes=held, fastest=True)
        return None if hauled is None else hauled["days"]

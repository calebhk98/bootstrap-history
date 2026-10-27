"""What starting a project costs now, all factors applied, and the frozen bill of one in hand.

Needs: price_index, state_interest, tree, material_cost_factor, project_material_parts, project_cost_without_materials,
legacy_projects."""
from . import constants, cost_rules


class Costs:

	def cost_money_factor(self):
		"""What a denarius of QUOTED cost means, for spending purposes: the price level. The model is in REAL terms, so debasement
		(which destroys the value of cash, handled by the haircut on capital when it fires) does not move a real price; the
		fall of `money_real` is not applied here, which would double-count in the opposite direction."""
		return float(self.needs.price_index())

	def opposition_factor(self, node_id):
		"""Opposed work costs more: bribes, delay, a provincial site, a front man."""
		return cost_rules.opposition_factor(self.needs.state_interest(self.needs.tree_nodes()[node_id]), constants.OPPOSITION_COST_PER_UNIT)

	def project_cost(self, node_id):
		"""What this project will actually cost in money, all factors applied: the number `why` quotes and the number the project
		must have actually PAID before it can complete (money must not be decorative, with only hours real)."""
		frozen = (self.needs.legacy_projects().active.get(node_id) or {}).get("bill")
		if frozen is not None:
			return frozen
		return self.project_cost_now(node_id)

	def project_cost_now(self, node_id):
		"""The cost if the project started today: labour and capital, plus the materials you do not already hold at current
		market prices."""
		needs = self.needs
		materials, _up_front = needs.project_material_parts[node_id]
		return cost_rules.cost_if_started_now(needs.project_cost_without_materials(node_id), materials,
		                                      needs.material_cost_factor(node_id), self.opposition_factor(node_id))

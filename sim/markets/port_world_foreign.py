"""The port's reads of the partner countries, the freight terms and the deposits."""
from sim.foreign_trade.api import SettleTraderCargo
from sim.resources.api import DrawDeposit


class ForeignReads:
	"""One member per view of the foreign trade, freight and resources owners the port asks. `PortWorld.foreign` holds it."""

	def __init__(self, needs):
		self._needs = needs

	def partners_in_agent_economy(self):
		return self._needs.partners_in_agent_economy()

	def foreign_economy_facts(self, civilization_id):
		return self._needs.partner_facts[civilization_id]

	def partner_price_per_unit(self, partner, material):
		return self._needs.partner_price_per_unit(partner, material)

	def actors_carry(self, material, to_partner, partner=None):
		return self._needs.actors_carry(material, to_partner, partner)

	def cargo_legs(self):
		return self._needs.cargo_legs()

	def settle_trader_cargo(self, results):
		return self._needs.send(SettleTraderCargo(results))

	# ---- freight ----

	def freight_mode_costs(self, imbalance=1.0, modes=None, cargo=None):
		return self._needs.freight_mode_costs(imbalance, modes, cargo)

	def material_carriage_per_tonne(self, material, price_per_tonne):
		return self._needs.material_carriage_per_tonne(material, price_per_tonne)

	# ---- the deposits ----

	def found_deposits(self, material):
		return self._needs.found_deposits[material]

	def partner_deposits(self, material, tile_ids):
		return self._needs.partner_deposits(material, tile_ids)

	def draw_deposit(self, deposit_id, tonnes):
		return self._needs.send(DrawDeposit(deposit_id, tonnes))

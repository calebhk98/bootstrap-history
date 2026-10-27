"""The port's reads of the partner countries, the freight and trader terms, the coin and the deposits."""
from sim.foreign_trade.api import SettleTraderCargo
from sim.resources.api import DrawDeposit


class ForeignReads:

	def partners_in_agent_economy(self):
		return self._needs.partners_in_agent_economy()

	def foreign_economies(self):
		return self._needs.foreign_economies()

	def partner_civ(self, civilization_id):
		return self._needs.partner[civilization_id]["civ"]

	def _foreign_economy_facts(self, civilization_id):
		return self._needs.partner_facts[civilization_id]

	def foreign_supply_tonnes(self, civilization_id, material):
		return self._needs.foreign_supply_tonnes(civilization_id, material)

	def foreign_lift_left_tonnes(self, civilization_id, route):
		return self._needs.lift_left_tonnes(civilization_id, route)

	def partner_price_per_unit(self, partner, material):
		return self._needs.partner_price_per_unit(partner, material)

	def actors_carry(self, material, to_partner, partner=None):
		return self._needs.actors_carry(material, to_partner, partner)

	def cargo_legs(self):
		return self._needs.cargo_legs()

	def settle_trader_cargo(self, results):
		return self._needs.send(SettleTraderCargo(results))

	# ---- freight and the traders' terms ----

	def _foreign_route(self, civilization, imbalance=None, cargo="goods"):
		return self._needs.foreign_route(civilization, imbalance, cargo)

	def _freight_mode_costs(self, imbalance=1.0, modes=None, cargo=None):
		return self._needs.freight_mode_costs(imbalance, modes, cargo)

	def material_carriage_per_tonne(self, material, price_per_tonne):
		return self._needs.material_carriage_per_tonne(material, price_per_tonne)

	def _trader_margin_share(self, civilization_id, route, price_flexibility=None):
		return self._needs.trader_margin_share(civilization_id, route, price_flexibility)

	def _cargo_lost_share(self, route, material=None, civilization_id=None, destination_demand_tonnes=None):
		return self._needs.cargo_lost_share(route, material, civilization_id, destination_demand_tonnes)

	def _trader_cycle_years(self, route, civilization_id=None, destination_demand_tonnes=None):
		return self._needs.trader_cycle_years(route, civilization_id, destination_demand_tonnes)

	def _agent_cost_per_tonne(self, civilization_id, route):
		return self._needs.trader_agent_cost(civilization_id, route)

	# ---- the partners' coin and the deposits ----

	def partner_price_level(self, civilization_id):
		return self._needs.partner_price_level[civilization_id]

	def _partner_coin_opening_units(self, civilization_id):
		return self._needs.partner_coin_opening[civilization_id]

	def foreign_coin_partner_units(self, partner):
		return self._needs.foreign_coin_partner_units[partner]

	def found_deposits(self, material):
		return self._needs.found_deposits[material]

	def partner_deposits(self, material, tile_ids):
		return self._needs.partner_deposits(material, tile_ids)

	def draw_deposit(self, deposit_id, tonnes):
		return self._needs.send(DrawDeposit(deposit_id, tonnes))

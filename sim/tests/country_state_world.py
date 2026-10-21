"""The home world's answers a country's state asks of it (prices, equipment, the market, the levy rule), for tests
that run a state's year without a game. A test that needs a different answer subclasses it in its own file."""
from .agents_fake_world import FakeWorld


class StateWorld(FakeWorld):
	year = 100

	def commodity_of(self, material):
		return material

	def material_cost(self, material, tonnes):
		return 2.0 * tonnes

	def material_price(self, material):
		return 2.0

	def equipment_kg_per_soldier(self):
		return 3.0

	def military_work_ids(self):
		return ()

	def equipment_kg_at_adoption(self, adoption):
		return 3.0

	def seat_taxpayers(self, country):
		return []

	def subsistence_kg_per_person_year(self):
		return 200.0

	def trade_exists(self, trade):
		return True

	def fleet_goods(self, holder_id=None):
		return []

	def output_tonnes(self, material, tiles=None):
		return 0.0

	def nodes_with_mechanic(self, mechanic):
		return []

	def state_weights(self):
		return {}

	def coin_regime(self):
		return "commodity"

	def visible_scale_of(self, actor):
		return 1.0

	def notice_over(self, scale, capacity=None):
		return 1.0

	def levy_shares(self, scale, protection=0.0, state=None):
		"""The home rule when no country's state is named; a country's own capacity and tax share otherwise."""
		return (0.99, 0.0) if state is None else (state[0] * state[1] + state[2], state[3])

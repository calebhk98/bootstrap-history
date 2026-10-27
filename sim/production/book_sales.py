"""Which of the acting seat's concerns sell in the agent economy's book, and what they put in and take out of it.

A concern whose goods the economy trades is paid what the year's clearing pays for the units buyers took
(economy_port_year `_settle_seats`), like a firm's plant; the engine's estimate (`revenue`) covers only the rest.
The offer and the inputs bought are one rule here, read by the clearing, the estimate and the forecast alike.
Needs: legacy_game."""
from . import concern_sales


class BookSales:

	def concern_book_scale(self, node_id):
		"""The share of the concern's full-staffing year it runs now: its ramp, size and the hazard and war factor."""
		game = self._game()
		units = self.institution_units(node_id) if node_id in game.SCALABLE_INSTITUTIONS else 1.0
		return self.venture_ramp(node_id) * units * game.output_factor

	def concern_book_offer(self, node_id):
		"""{material: units} the concern puts in this year's clearing; empty for a concern the engine's estimate covers
		(not running as the acting seat's own, makes nothing from output, or nothing it makes is traded)."""
		game = self._game()
		projects = game.state.projects
		if node_id not in projects.operating or node_id in projects.granted or not self.is_venture(node_id):
			return {}
		baskets = self.concern_baskets_now(node_id)
		if baskets is None:
			return {}
		return concern_sales.offered_units(baskets.outputs, self.concern_book_scale(node_id), game.economy.agent_trades_good)

	def concern_sells_on_book(self, node_id):
		"""Whether the clearing pays this concern, so the estimate leaves it out."""
		return bool(self.concern_book_offer(node_id))

	def concern_book_inputs_cost(self, node_id):
		"""What the concern's year of inputs costs at the economy's prices, charged to the seat because the clearing
		pays the gross of its sales (the estimate was net of them); a price the economy lacks falls back to the
		long-run cost at today's price level."""
		game = self._game()
		baskets = self.concern_baskets_now(node_id)
		if baskets is None:
			return 0.0

		economy_prices = game.economy.agent_prices_at() or {}

		def price_of(material):
			key = game._priced_key(material, economy_prices)
			if key is not None:
				return economy_prices[key]
			cost = game._material_prices().get(material)    # read only for a good the economy has no price for
			return None if cost is None else cost * game.price_index
		return concern_sales.inputs_cost(baskets.purchases, self.concern_book_scale(node_id), price_of)

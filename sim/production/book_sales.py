"""Which of the acting seat's concerns sell in the agent economy's book, and what they put in and take out of it.

A concern whose goods the economy trades is paid what the year's clearing pays for the units buyers took
(economy_port_year `_settle_seats`), like a firm's plant; the engine's estimate (`revenue`) covers only the rest.
The offer and the inputs bought are one rule here, read by the clearing, the estimate and the forecast alike.
Needs: the views of READS_BY_OWNER in module_spec.py."""
from sim.prices.api import rules as price_rules

from . import concern_sales


class BookSales:

	def concern_book_scale(self, node_id):
		"""The share of the concern's full-staffing year it runs now: its ramp, size and the hazard and war factor."""
		units = self.institution_units(node_id) if node_id in self.needs.capability_sets()[1] else 1.0
		return self.venture_ramp(node_id) * units * self.needs.output_factor()

	def concern_book_offer(self, node_id):
		"""{material: units} the concern puts in this year's clearing; empty for a concern the engine's estimate covers
		(not running as the acting seat's own, makes nothing from output, or nothing it makes is traded)."""
		if node_id not in self.needs.projects_operating() or node_id in self.needs.techniques_granted() or not self.is_venture(node_id):
			return {}
		baskets = self.concern_baskets_now(node_id)
		if baskets is None:
			return {}
		trades_good = self.needs.agent_trades_good
		return concern_sales.offered_units(baskets.outputs, self.concern_book_scale(node_id), lambda material: trades_good[material])

	def concern_sells_on_book(self, node_id):
		"""Whether the clearing pays this concern, so the estimate leaves it out."""
		return bool(self.concern_book_offer(node_id))

	def concern_book_inputs_cost(self, node_id):
		"""What the concern's year of inputs costs at the economy's prices, charged to the seat because the clearing
		pays the gross of its sales (the estimate was net of them); a price the economy lacks falls back to the
		long-run cost at today's price level."""
		needs = self.needs
		baskets = self.concern_baskets_now(node_id)
		if baskets is None:
			return 0.0

		economy_prices = needs.agent_prices_at() or {}

		def price_of(material):
			key = price_rules.priced_key(material, economy_prices, needs.commodity_record[material])
			if key is not None:
				return economy_prices[key]
			cost = needs.material_prices().get(material)    # read only for a good the economy has no price for
			return None if cost is None else cost * needs.price_index()
		return concern_sales.inputs_cost(baskets.purchases, self.concern_book_scale(node_id), price_of)

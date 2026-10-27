"""What a concern sells at and takes in: whether the economy prices its goods, the market over long-run price for what it makes
and buys, what the share counted as sold stands on, and its takings and upkeep at a given ramp and capacity.
Needs: legacy_game, money_per_labour_hour."""
from . import concern_sales, node_revenue_market
from .concern_earnings import output_market_factor, takings_at


class ConcernMarket:

	def priced(self, hours):
		"""A count of labour hours as money in the civilisation's coin."""
		return hours * self.needs.money_per_labour_hour()

	def concern_goods_have_market(self, node_id):
		"""Whether the economy prices what the concern sells; a good nobody has sold yet has none, and its
		quote then values sales and purchases alike at long-run cost rather than mixing the two bases."""
		game = self._game()
		baskets = self.concern_baskets_now(node_id)
		paid = game.economy.agent_prices_at()
		if baskets is None or paid is None:
			return True
		return all(game._priced_key(material, paid) is not None for material in baskets.outputs)

	def node_output_market_factor(self, node, selling_seat=None):
		"""This year's market over long-run prices for what an output-derived node sells and buys; one otherwise.
		`selling_seat` names the seat whose concern it is: only the share its output sold in the clearing counts, at
		the price it cleared at (concern_sales.py); without it every unit sells at the sellers' ask."""
		game = self._game()
		baskets = self.concern_baskets_now(node["id"])
		outlook = None if selling_seat is None else (
			lambda material, quantity: game.economy.agent_seat_sale_outlook(selling_seat, material, quantity))
		return output_market_factor(
			baskets is not None and self.concern_goods_have_market(node["id"]),
			lambda: node_revenue_market.basket_market_factor(
				baskets.outputs, baskets.purchases, game._material_prices(), game.goods_market.home_unit_price, outlook))

	def basket_market_factor(self, sold, bought, long_run_prices, price_now):
		return node_revenue_market.basket_market_factor(sold, bought, long_run_prices, price_now)

	def concern_sale_basis(self, node_id):
		"""What the share of a founder concern's output counted as sold stands on: `cleared_last_year` (its own sales
		in the last clearing), `buyers_last_year` (what the market's buyers took and still wanted, before it has sold),
		or `no_market_yet` (nobody trades its goods, so every unit is counted at long-run cost)."""
		game = self._game()
		baskets = self.concern_baskets_now(node_id)
		if baskets is None or not self.concern_goods_have_market(node_id):
			return concern_sales.NO_MARKET_YET
		seat = game.state.acting_seat
		bases = [taken.basis for material, units in sorted(baskets.outputs.items()) if units > 0.0
		         for taken in [game.economy.agent_seat_sale_outlook(seat, material, units)] if taken is not None]
		if not bases:
			return concern_sales.NO_MARKET_YET
		return concern_sales.CLEARED_LAST_YEAR if all(basis == concern_sales.CLEARED_LAST_YEAR for basis in bases) \
			else concern_sales.BUYERS_LAST_YEAR

	def concern_takings(self, node_id, ramp, with_output_factor=True, cost_scale=None):
		"""Yearly takings of one concern at a given ramp, before market saturation: its loaded figure
		carried to the techniques held now (volume.py); callers apply the market's price.
		`with_output_factor` False leaves out the hazard and war factor `revenue` applies to its total;
		`cost_scale` is the scale on the tree's book coin (the home society's when none is given)."""
		game = self._game()
		return takings_at(game.nodes[node_id]["rev"], ramp, game.output_factor if with_output_factor else 1.0,
		                  game.price_index if cost_scale is None else cost_scale, self.concern_value_ratio(node_id),
		                  self.concern_learning_ratio(node_id))

	def concern_gross(self, node_id):
		"""Yearly takings of a concern once ramped up, with the market's price for its goods applied."""
		return self._game().economy.concern_gross(node_id)

	def concern_upkeep(self, node_id, capacity=1.0, **options):
		"""Yearly upkeep of a concern at a given capacity, without its crew's pay (an actor that runs a concern hires the crew
		through the labour market and pays wages there)."""
		return self._game().economy.concern_upkeep(node_id, capacity, **options)

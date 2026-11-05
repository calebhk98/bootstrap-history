"""The agent economy's price views: goods prices, the rate, credit room, the price response and the money values."""
from . import port_money
from .agent_view_part import AgentViewPart


class AgentPriceViews(AgentViewPart):

	def agent_prices(self):
		"""{good: the agent economy's price now}, or None while the economy opens."""
		return self.parts.market_objects.economy.agent_prices()

	def agent_prices_at(self, tile=None):
		"""{good: the agent economy's price in coin} on a tile (the acting one by default), or None while the economy opens."""
		return self.parts.market_objects.economy.agent_prices_at(tile)

	def agent_seat_sale_outlook(self, seat_id, material, quantity):
		"""What a seat may count as sold of `quantity` units of a material its concerns make; None while the economy opens."""
		parts = self._answering()
		return None if parts is None else parts.seats.sale_outlook(seat_id, material, quantity)

	def agent_price_response(self, material, landed_tonnes, taken_tonnes):
		return self.parts.market_objects.economy.agent_price_response(material, landed_tonnes, taken_tonnes)

	def agent_rate(self):
		"""The agent economy's loanable-funds rate, or None while it opens."""
		parts = self._answering()
		return None if parts is None else parts.prices.rate()

	def agent_credit_room(self, borrower_id):
		"""(True, room) when the agent economy answers, with room None before lenders have met; (False, None) while it opens."""
		parts = self._answering()
		return (False, None) if parts is None else (True, parts.prices.credit_room(borrower_id))

	def agent_fundable_amount(self, amount, existing_debt, collateral_value, arrears):
		"""(True, the most of a draw of `amount` coin the credit market lends an actor that owes `existing_debt`, None before
		lenders have met) when the agent economy answers; (False, None) while it opens."""
		parts = self._answering()
		return (False, None) if parts is None else (True, parts.prices.fundable_amount(amount, existing_debt, collateral_value, arrears))

	def agent_risk_premium(self, debt_after, collateral_value, arrears):
		"""(True, the rate added to the market rate for that debt) when the agent economy answers; (False, None) while it opens."""
		parts = self._answering()
		return (False, None) if parts is None else (True, parts.prices.risk_premium(debt_after, collateral_value, arrears))

	def agent_lender_listing(self):
		"""(True, the lenders of the last lending) when the agent economy answers; (False, None) while it opens. The listing is
		{"currency", "coin_per_unit", "lenders": [(lender, offer, capacity, balance, ask)]} cheapest ask first, in the economy's units."""
		parts = self._answering()
		return (False, None) if parts is None else (True, parts.prices.lender_listing())

	def fleet_goods(self, holder_id):
		return self.parts.market_objects.economy.fleet_goods(holder_id)

	def economy_output_value(self):
		return port_money.output_value(self._economy())

	def coin_stock_value(self):
		return port_money.coin_stock_value(self._economy())

"""The views of what the acting seat's own hours earn and what the market asks for a year of a trade."""


class StandingViews:

	def wage_signature(self):
		"""A cheap fingerprint of what moves a trade's market wage within a year, for a figure cached over `standing_job_pay`."""
		return self.labour.wage_signature()

	def market_annual_wage(self, trade):
		"""Money one person-year of a trade costs on the home labour market now."""
		return self.labour.market.quote_annual(trade)

	def standing_job_pay(self, trade):
		"""A year of the seat's unspoken-for hours sold in `trade` at its market wage; nothing without a trade."""
		return self.labour.standing_job_pay(trade)

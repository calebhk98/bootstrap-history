"""The views the workforce module publishes that answer a fact of its labour implementation."""
from . import rules


class FactViews:

	def wage_bill(self):
		"""What the seat's standing staff costs every year, by trade."""
		return self.labour.wage_bill()

	def unskilled_trade(self):
		"""The registry's flagged fallback trade: the one anyone can take up at once."""
		return self.labour.unskilled_trade()

	def settlement_tiles(self):
		"""{tile id: people living there} for the tiles the nation holds."""
		return self.labour.settlement_tiles()

	def labour_need_shares(self):
		"""{trade: share of the hours the society's needs ask of it}."""
		return self.labour.need_shares()

	def opening_wage_index(self):
		"""The wage index of the civilisation's opening year, which the index is measured against."""
		return rules.opening_wage_index(self.needs.civilisation())

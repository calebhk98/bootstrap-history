"""The views the workforce module publishes that answer a fact of its labour implementation."""
from sim.assembly.api import Part
from sim.labour.api import wage_provider

from . import rules
from .wage_schedule import build_schedule


class FactViews(Part):

	def __init__(self, module):
		super().__init__(module)
		self._starting_wages = None  # the reference civilisation's opening wages, worked out when first asked; never saved

	def starting_wages(self):
		"""{trade: money an hour pays} on the reference civilisation's opening schedule."""
		if self._starting_wages is None:
			self._starting_wages = build_schedule(self.needs.trade_records(), wage_provider.reference_civilisation()).wages_per_hour()
		return self._starting_wages

	def wage_schedule_for(self, civ):
		"""The wage schedule a civilisation opens on, built from the trade registry and the price solver."""
		return build_schedule(self.needs.trade_records(), civ)

	def wages_charged_last_year(self):
		"""What the last clearing charged the acting seat for its staff and one-year orders; before any clearing, the payroll
		the staff on the books would cost at the market wage."""
		paid = self.seat.wages_paid
		return self.parts.core.labour.wages.wage_bill() if paid is None else paid

	def wage_bill(self):
		"""What the seat's standing staff costs every year, by trade."""
		return self.parts.core.labour.wages.wage_bill()

	def unskilled_trade(self):
		"""The registry's flagged fallback trade: the one anyone can take up at once."""
		return self.parts.core.labour.allocation.unskilled_trade()

	def settlement_tiles(self):
		"""{tile id: people living there} for the tiles the nation holds."""
		return self.parts.core.labour.settlement.settlement_tiles()

	def labour_need_shares(self):
		"""{trade: share of the hours the society's needs ask of it}."""
		return self.parts.core.labour.allocation.need_shares()

	def opening_wage_index(self):
		"""The wage index of the civilisation's opening year, which the index is measured against."""
		return rules.opening_wage_index(self.needs.civilisation())

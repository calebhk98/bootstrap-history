"""What worker housing and a trade-school seat cost now, and how many people the household keeps besides the founder.

Needs: money_per_labour_hour (this module's), price_index, staff (this module's)."""
from . import constants, rules


class HousingPrices:

	def trade_school_price_per_seat(self):
		"""What one trade-school seat costs now (`buy school`, `quote school`)."""
		return rules.price_of_labour_hours(constants.TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT, self.money_per_labour_hour(),
		                                   self.needs.price_index())

	def housing_price_per_place(self):
		"""What one place of worker housing costs now (`buy housing`, `quote housing`, room advice)."""
		return rules.price_of_labour_hours(constants.HOUSING_LABOUR_HOURS_PER_PLACE, self.money_per_labour_hour(),
		                                   self.needs.price_index())

	def household_dependant_people(self):
		"""People the household keeps besides the founder: each a person with needs of their own."""
		staff = self.staff()
		return rules.dependant_people(constants.HOUSEHOLD_DEPENDANT_PEOPLE, staff["freedmen"], staff["slaves"])

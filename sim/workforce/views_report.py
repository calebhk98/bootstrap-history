"""The views the workforce module publishes for what the screens tell the player about its people: room, hours, quotes and reports."""
from sim.assembly.api import Part
from sim.labour.api import hours_by_trade_of_all_employers, people_by_trade_of_all_employers


class ReportViews(Part):

	# ---- what the seat has posted in the labour core, read by the markets module when it clears ----

	def staff_posting(self):
		"""{trade: people} the acting seat has posted in the labour core: the places its staff are hired into."""
		return self.parts.core.labour.book.staff_posting()

	def once_posting(self):
		"""{purpose: {trade: hours}} the acting seat asks the labour core for this year only."""
		return self.parts.core.labour.book.once_posting()

	def wage_work_offered(self):
		"""{trade: hours} the acting seat offers of its own in the labour core this year."""
		return self.parts.core.labour.book.wage_work_offered()

	def newcomers(self):
		"""{trade: people} trained or granted since the last clearing who are not yet in the labour core."""
		return self.parts.core.labour.book.newcomers()

	def employed_by_trade(self):
		"""A copy of the acting seat's staff, trade to head count."""
		return self.parts.core.labour.book.employed_by_trade()

	def occupation_people_by_trade(self):
		"""Working people by main occupation across every employer; None while the agent economy has not opened."""
		return people_by_trade_of_all_employers(self.parts.core.labour)

	def occupation_hours_by_trade(self):
		"""The year's hours by trade across every employer."""
		return hours_by_trade_of_all_employers(self.parts.core.labour, self.world.society_labour_hours)

	# ---- room and supervision ----

	def household_room(self):
		"""How many more people the household can take on (negative when it is over)."""
		return self.parts.core.labour.capacity.household_room()

	def room_advice(self):
		"""What raises the household's room, in words."""
		return self.parts.core.labour.advice.room_advice()

	def supervision_room(self):
		"""How many people the seat's directors can oversee."""
		return self.parts.core.labour.capacity.supervision_room()

	def supervision_room_from(self):
		"""Where the supervision room comes from."""
		return self.parts.core.labour.capacity.supervision_room_from()

	def sole_supervisors(self):
		"""The concerns that depend on a single person."""
		return self.parts.core.labour.ledger.sole_supervisors()

	def idle_specialists(self):
		"""The specialists with no work to do."""
		return self.parts.core.labour.ledger.idle_specialists()

	# ---- reports ----

	def population_report(self):
		return self.parts.core.labour.report.population_report()

	def workforce_report(self):
		return self.parts.core.labour.ledger.workforce_report()

	def craft_trades_report(self):
		return self.parts.core.labour.trades.craft_trades_report()

	def wage_work_this_year(self):
		"""What the seat has earned this year working for wages."""
		return self.parts.core.labour.wages.wage_work_this_year()

	def home_town_population_estimate(self):
		return self.parts.core.labour.settlement.home_town_population_estimate()

	def literate_trades(self):
		"""The trades that need reading and writing (answers `in` and iteration)."""
		return self.parts.core.labour.trades.LITERATE_TRADES

	def slave_base_price(self):
		"""What one enslaved person costs before the number bought raises it."""
		return self.parts.core.labour.bondage.SLAVE_BASE_PRICE

	# ---- a trade ----

	def hours_reserved(self, trade):
		return self.parts.core.labour.hands.hours_reserved(trade)

	def hours_hired_once(self, purpose):
		"""{trade: hours} the last clearing hired for the acting seat's one-year order of a purpose."""
		return dict(self.seat.hours_hired_once.get(purpose, {}))

	def trade_headcount_pending(self, trade):
		return self.parts.core.labour.book.trade_headcount_pending(trade)

	def literacy_factor(self, trade):
		return self.parts.core.labour.trades.literacy_factor(trade)

	def training_hours_per_person(self, trade, source=None):
		return self.parts.core.labour.training.training_hours_per_person(trade, source)

	# ---- what an order would do, asked before it is sent ----

	def hire_check(self, trade, count):
		return self.parts.core.labour.hiring.hire_check(trade, count)

	def commission_check(self, trade, hours):
		return self.parts.core.labour.commissions.commission_check(trade, hours)

	def train_check(self, trade, count, source=None):
		return self.parts.core.labour.training.train_check(trade, count, source)

	def trainee_wage_bill(self, trade, count):
		return self.parts.core.labour.training.trainee_wage_bill(trade, count)

	def work_for_wages_dry_run(self, trade, hours):
		return self.parts.core.labour.wages.work_for_wages_dry_run(trade, hours)

	def relocation_quote(self, tile):
		return self.parts.core.labour.relocation.relocation_quote(tile)

	def slave_quote(self, people):
		return self.parts.core.labour.bondage.slave_quote(people)

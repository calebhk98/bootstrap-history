"""The views the workforce module publishes for what the screens tell the player about its people: room, hours, quotes and reports."""


class ReportViews:

	# ---- room and supervision ----

	def household_room(self):
		"""How many more people the household can take on (negative when it is over)."""
		return self.labour.household_room()

	def room_advice(self):
		"""What raises the household's room, in words."""
		return self.labour.room_advice()

	def supervision_room(self):
		"""How many people the seat's directors can oversee."""
		return self.labour.supervision_room()

	def supervision_room_from(self):
		"""Where the supervision room comes from."""
		return self.labour.supervision_room_from()

	def sole_supervisors(self):
		"""The concerns that depend on a single person."""
		return self.labour.sole_supervisors()

	def idle_specialists(self):
		"""The specialists with no work to do."""
		return self.labour.idle_specialists()

	# ---- reports ----

	def population_report(self):
		return self.labour.population_report()

	def workforce_report(self):
		return self.labour.workforce_report()

	def craft_trades_report(self):
		return self.labour.craft_trades_report()

	def wage_work_this_year(self):
		"""What the seat has earned this year working for wages."""
		return self.labour.wage_work_this_year()

	def home_town_population_estimate(self):
		return self.labour.home_town_population_estimate()

	def literate_trades(self):
		"""The trades that need reading and writing (answers `in` and iteration)."""
		return self.labour.LITERATE_TRADES

	def slave_base_price(self):
		"""What one enslaved person costs before the number bought raises it."""
		return self.labour.SLAVE_BASE_PRICE

	# ---- a trade ----

	def market_supply_split(self, trade):
		return self.labour.market_supply_split(trade)

	def hours_reserved(self, trade):
		return self.labour.hours_reserved(trade)

	def trade_headcount_pending(self, trade):
		return self.labour.trade_headcount_pending(trade)

	def literacy_factor(self, trade):
		return self.labour.literacy_factor(trade)

	def training_hours_per_person(self, trade, source=None):
		return self.labour.training_hours_per_person(trade, source)

	# ---- what an order would do, asked before it is sent ----

	def hire_check(self, trade, count):
		return self.labour.hire_check(trade, count)

	def commission_check(self, trade, hours):
		return self.labour.commission_check(trade, hours)

	def train_check(self, trade, count, source=None):
		return self.labour.train_check(trade, count, source)

	def trainee_wage_bill(self, trade, count):
		return self.labour.trainee_wage_bill(trade, count)

	def work_for_wages_dry_run(self, trade, hours):
		return self.labour.work_for_wages_dry_run(trade, hours)

	def relocation_quote(self, tile):
		return self.labour.relocation_quote(tile)

	def slave_quote(self, people):
		return self.labour.slave_quote(people)

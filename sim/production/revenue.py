"""Revenue, the founder's job and workshops.

Every method here answers "what does the household actually take in this year", as opposed to the price solver's question of what a unit
of output sells for once made: `revenue_capacity`, `revenue` and `revenue_sources` (what a household earns, itemised),
`workshop_output` and `capability_factor` (what a staffed workshop makes, and how accumulated method multiplies it),
`venture_ramp` and `still_ramping` (how a concern's takings ramp up after it opens), `held_trade` and `founder_wage_income`, and
the held-skill and candidate-set caches that `revenue` and `upkeep` share.

The caches are the module's own per seat (`memos`); the engine's household hooks drop them by sending the commands in commands.py.
Needs: the views of READS_BY_OWNER in module_spec.py."""
from sim.world import plant_figures

from sim.workforce.api import SetWageHoursSold

from . import rules
from .bondage_workshop_rules import workshop_craft_wages, workshop_output_value
from .concern_earnings import ledger_row
from .constants import (RAMP_SHARE_AT_FULL_DEPTH, REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE, SLAVE_LABOUR_PRODUCTIVITY_SHARE,
                        WORKSHOP_WAGE_MARKUP_BASE)
from .revenue_ledger import assemble_ledger


class Revenue:

	def venture_ramp(self, node_id):
		"""How much of its full takings a concern is making, 0..1.

		FROM THE YEAR YOU OPENED IT, not the year you worked out how: a concern built in one year and opened years later must
		still ramp up from its opening, or delaying `open` would be strictly better than opening promptly. Custom takes time to
		find whoever owns the shop.
		"""
		year = self.needs.year()
		started = self.needs.venture_opened_year(node_id, None)
		if started is None:
			started = self.needs.done_year().get(node_id, year)
		age = year - started
		# An established industry (anyone's worker-years running it) finds its custom sooner.
		return plant_figures.ramp(age, self.needs.game_setting["revenue_ramp_years"], self.industry_depth(node_id),
		                          RAMP_SHARE_AT_FULL_DEPTH)

	def revenue_capacity(self):
		"""What you would earn in an ordinary year, with your own hands on your own work, none of this year's hours sold on
		request. Used where a swing in ONE year should not count - a lender does not cut your line because you took a job this year."""
		_sold = self.needs.hour_commitments()["wage_hours"]
		self.needs.send(SetWageHoursSold(0.0))
		try:
			return self.revenue()
		finally:
			self.needs.send(SetWageHoursSold(_sold))

	def revenue(self):
		"""Total annual revenue across all active concerns, workshops, and state funding.

		Cached on the household under a key of everything it reads: the year, the population scale, output per head, the versions
		of what is done, operating, staffed and scaled, the hours sold on request and committed, the market wage's recent hiring,
		the own hours the standing job sells, the household's farmland, standing, the hazard factor, whether the founder lives,
		state funding and the price level. Any change to the key recomputes it; the engine also drops it with the other economic caches.
		"""
		needs = self.needs
		standing = needs.standing()
		staff = needs.staff()
		done_version, operating_version, units_version = needs.techniques_version(), needs.operating_version(), needs.institution_units_version()
		key = (
			needs.year(),
			needs.pop_scale(),
			needs.real_output_per_head(),
			operating_version,
			done_version,
			needs.staff_version(),
			units_version,
			needs.hour_commitments()["wage_hours"],
			needs.hours_available["director_committed"],
			needs.wage_signature(),
			staff["directors_extra"],
			needs.debt_status()["bondage_years_left"],
			needs.farm_holdings()["hectares"] or 0.0,
			staff["freedmen"] or 0.0,
			staff["slaves"] or 0.0,
			standing["governance"] or 0.0,
			needs.output_factor(),
			standing["reputation"],
			needs.founder()["alive"],
			needs.state_funding(),
			needs.home_price_level(),
		)
		memos = self.memos()
		if memos.revenue_key != key:
			memos.revenue_value = self._compute_revenue_uncached()
			memos.revenue_key = key
		return sum(memos.revenue_value)

	def estimated_revenue(self):
		"""The part of `revenue` the engine credits as an estimate: everything but the concerns the clearing pays
		(book_sales.py). The year's ledger credits this; those concerns are credited by the clearing."""
		self.revenue()
		return self.memos().revenue_value[0]

	def concern_revenue(self, node_id):
		"""What one open concern earns in a year before the output factor: the figure the screens quote."""
		return self.needs.venture_real_earnings(node_id, None, False, False)

	def _compute_revenue_uncached(self):
		"""(the estimate, the forecast of the concerns the clearing pays), both after the output factor."""
		needs = self.needs
		total_revenue = 0.0
		book_forecast = 0.0
		practice_set = self._practice_set()
		nodes = needs.tree_nodes()
		granted = needs.techniques_granted()
		operating = needs.operating()
		# Scan only what could possibly pay: a node that is neither operating nor practised is skipped below, and was already
		# skipped for the whole rest of `done`, which only grows (see _revenue_upkeep_candidates).
		for node_id in self._revenue_upkeep_candidates():
			practice = node_id in practice_set
			if node_id in granted and not practice:
				continue          # the society's, not yours
			# Knowing how is not running it: a node pays when it is open, and not for having been worked out.
			if not practice and node_id not in operating:
				continue
			node = nodes[node_id]
			# a held skill earns through the founder's own hours (founder_wage_income), not through the node
			if node["rev"] and not practice:
				if self.concern_sells_on_book(node_id):
					book_forecast += self.concern_revenue(node_id)    # last year's sale record, as the clearing paid it
				else:
					total_revenue += self.concern_revenue(node_id)
		# There is only so much market for what the clearing does not pay. Uncapped, this compounds: every venture pays back
		# quickly, so its income buys the next one. A saturating curve caps that without ever making a venture worthless.
		# What your own workshop sells: a payroll without credited output is pure cost, and it needs somewhere to work.
		total_revenue += self.workshop_output()
		total_revenue += self.founder_wage_income()
		gross = total_revenue
		ceiling = self.priced(REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE) * needs.pop_scale() \
			* needs.real_output_per_head() * needs.price_index()
		gross = rules.saturated_revenue(gross, ceiling)
		return (gross + needs.state_funding()) * needs.output_factor(), book_forecast * needs.output_factor()

	def workshop_output(self):
		"""What your standing staff produce and sell, over and above projects."""
		needs = self.needs
		if not needs.running_mechanics("workshop_site"):
			return 0.0
		staff = needs.staff()
		annual_wage = needs.market_annual_wage
		wage = workshop_craft_wages(
			staff["employees"], lambda trade: needs.trade_family[trade] == "craft", lambda trade: annual_wage[trade],
			staff["freedmen"] + staff["slaves"] * SLAVE_LABOUR_PRODUCTIVITY_SHARE, annual_wage["artisan"])
		mark = WORKSHOP_WAGE_MARKUP_BASE
		mark = needs.effect_sum("workshop_markup", mark)
		# Knowing how to do a thing earns nothing on its own; it makes the workshop you staff and pay for more productive,
		# which is how method has always paid. It needs a workshop and it needs people; with neither it is worth nothing.
		return workshop_output_value(wage, mark, self.capability_factor())

	def capability_factor(self):
		"""How much better your methods make the same pair of hands.

		Tier-weighted, over what you have built and are NOT separately running as a concern - a concern already pays you
		directly and must not be counted twice. Saturating, because the tenth improvement to a workshop is worth less than
		the first.

		Cached in the module's memos: the finished result of exactly this walk, recomputed from scratch whenever done or operating
		change (`RefreshDoneCaches`, `RefreshOperatingCaches` clear it), so it is bit-identical to an uncached call. An incremental total
		would drift in its last bits, since float addition is not associative and the order nodes enter or leave is not the
		order `done_in_order` walks them in.
		"""
		memos = self.memos()
		cached = memos.capability_factor
		if cached is not None:
			return cached
		weight = 0.0
		nodes = self.needs.tree_nodes()
		granted = self.needs.techniques_granted()
		operating = self.needs.operating()
		for node_id in self.done_in_order():
			if node_id in granted or node_id in operating:
				continue
			node = nodes[node_id]
			if node["rev"] <= 0:
				continue
			weight += node["rev_hours"]     # in hours, so the price level of money does not enter it
		result = rules.capability_factor(weight)
		memos.capability_factor = result
		return result

	def ledger_concern_rows(self):
		"""Yearly takings of every opened concern that earns, by node id, as the ledger credits them. The
		founder's own practice is one row of `revenue_sources`, not one per skill."""
		needs = self.needs
		rows = {}
		nodes = needs.tree_nodes()
		granted = needs.techniques_granted()
		operating = needs.operating()
		for node_id in self.done_in_order():
			if node_id in granted or node_id not in operating:
				continue
			if not nodes[node_id]["rev"]:
				continue
			# The figure `ventures` and `why` print, and the factor revenue() applies, so the ledger's parts add up to its total.
			row = ledger_row(needs.venture_real_earnings(node_id, None, False, True))
			if row is not None:
				rows[node_id] = row
		return rows

	def held_trade(self):
		"""The trade the founder sells hours in: scholar when a skill the founder holds asks for
		scholars, else artisan; None when the founder holds no skill."""
		held = self._practice_set()
		if not held:
			return None
		nodes = self.needs.tree_nodes()
		return "scholar" if any(nodes[node_id]["sch"] > 0 for node_id in held) else "artisan"

	def founder_wage_income(self):
		"""Yearly pay of the founder's standing job: the hours not spoken for, sold in the held trade at
		that trade's market wage (labour_job.py). One person's hours sell once however many skills the
		founder holds, and a dead founder sells none."""
		return self.needs.standing_job_pay[self.held_trade()]

	def revenue_sources(self):
		"""Where the money actually comes from, itemised.

		A player who never issues a single start can still get richer every year, from the wages of their own work - the
		founder is employed in a trade they hold - which is otherwise invisible anywhere else in the interface.
		"""
		needs = self.needs
		funding = needs.state_funding()
		return assemble_ledger(
			self.ledger_concern_rows(), self.workshop_output() * needs.output_factor(),
			self.founder_wage_income() * needs.output_factor(),
			funding * needs.output_factor() if funding > 0.5 else None, self.revenue())

	# A granted node whose category is flagged practisable is a skill the founder holds and works with their own hands; the held
	# skills choose the trade the founder's hours are sold in (held_trade). A granted fleet of merchant ships is owned by other
	# people, so shipping is not one.
	def _practisable(self, node_id):
		"""Is this granted node a skill the founder holds and works with their own hands?"""
		return self.needs.category_trait(self.needs.tree_nodes()[node_id].get("cat"), "practisable")

	def still_ramping(self):
		"""Earners that are not yet paying their full figure, and how far along.

		Every earner ramps over revenue_ramp_years, so on the day you open one it pays only a fraction of what the tree quotes
		for it. Nothing else explains that gap between the quoted figure and the ledger, so this surfaces it directly. Kept OUT
		of revenue_sources, whose every value is a number that has to sum to the revenue above it.
		"""
		needs = self.needs
		young = []
		nodes = needs.tree_nodes()
		granted = needs.techniques_granted()
		for node_id in sorted(needs.operating()):
			node = nodes.get(node_id)
			if not node or not node["rev"] or node_id in granted:
				continue
			ramp = self.venture_ramp(node_id)
			if ramp < 0.999:
				young.append((node_id, ramp))
		if not young:
			return None
		young.sort(key=lambda entry: entry[1])
		return ("%s%s at %d%% of full takings. A concern you open reaches its "
		        "full figure over %g years, so what the ledger shows is not "
		        "what it will be."
		        % (", ".join(node_id for node_id, _ramp in young[:6]),
		           " and %d more" % (len(young) - 6) if len(young) > 6 else "",
		           young[0][1] * 100, needs.game_setting["revenue_ramp_years"]))

	def _practice_set(self):
		"""The granted skills you actually practise, as a set, computed once: the answer never changes unless the granted
		set does, which happens at setup and never again. (`revenue` once called `_practisable` per done node per call.)"""
		granted = self.needs.techniques_granted()
		memos = self.memos()
		cache = memos.practice
		if cache is None or cache[0] != len(granted):
			cache = (len(granted), frozenset(node_id for node_id in granted if self._practisable(node_id)))
			memos.practice = cache
		return cache[1]

	def _revenue_upkeep_candidates(self):
		"""Every node in `done` that revenue() or upkeep() could possibly charge or pay for - operating, or in your practice
		set - in done_in_order()'s own tree order. Neither can do anything with a node that is neither, and scanning the whole
		of `done` (most of the tree by the late game) to throw almost all of it away is wasted work.

		Cached on three signals: the identity of done_in_order()'s cached list (a NEW list exactly when `done` changes; a length
		check is not safe, since a year that finishes one thing and abandons another leaves the length unchanged), the
		`operating` version counter, and the identity of `_practice_set`'s frozenset (new exactly when the granted set grows).
		Strong references and `is`, not bare id() integers: a freed object's address is handed straight to the next same-sized
		allocation, so two different objects compare equal by id() often enough to replay a stale answer.
		"""
		seq = self.done_in_order()
		practice_set = self._practice_set()
		operating_version = self.needs.operating_version()
		memos = self.memos()
		cached = memos.candidates
		if (cached is not None and cached[0] is seq
		        and cached[1] is practice_set and cached[2] == operating_version):
			return cached[3]
		operating = self.needs.operating()
		candidates = [node_id for node_id in seq if node_id in operating or node_id in practice_set]
		memos.candidates = (seq, practice_set, operating_version, candidates)
		return candidates

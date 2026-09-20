"""The outside-facing compatibility property surface for the authoritative SimulationState.

These properties provide backward-compatibility for external consumers and
integration test assertions. Internal simulation code accesses live state
directly through authoritative subsystem owners:
  - self.state.household
  - self.state.projects
  - self.state.economy
  - self.state.governance
  - self.state.founder
  - self.state.scenario
  - self.state.population

Properties are categorized strictly by owning subsystem.
"""
from typing import Any, Iterable, Set


class ForwardingPropertiesMixin:
	"""Composition point: backward-compatibility property facade delegating to
	authoritative subsystem live state.
	"""
	# =========================================================================
	# HouseholdState Compatibility Properties
	# =========================================================================

	@property
	def capital(self):
		return getattr(self.state.household, "capital")

	@capital.setter
	def capital(self, value):
		setattr(self.state.household, "capital", value)

	@property
	def hour_allocations(self):
		return getattr(self.state.household, "hour_allocations")

	@hour_allocations.setter
	def hour_allocations(self, value):
		setattr(self.state.household, "hour_allocations", value)

	@property
	def hours_this_year(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("hours_this_year")
		val = getattr(sub, "hours_this_year", None)
		if val is None:
			raise AttributeError("hours_this_year")
		return val

	@hours_this_year.setter
	def hours_this_year(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "hours_this_year", value)

	@property
	def wage_hours_this_year(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("wage_hours_this_year")
		val = getattr(sub, "wage_hours_this_year", None)
		if val is None:
			raise AttributeError("wage_hours_this_year")
		return val

	@wage_hours_this_year.setter
	def wage_hours_this_year(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "wage_hours_this_year", value)

	@property
	def teaching_hours_this_year(self):
		return getattr(self.state.household, "teaching_hours_this_year")

	@teaching_hours_this_year.setter
	def teaching_hours_this_year(self, value):
		setattr(self.state.household, "teaching_hours_this_year", value)

	@property
	def spend_last_year(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("spend_last_year")
		val = getattr(sub, "spend_last_year", None)
		if val is None:
			raise AttributeError("spend_last_year")
		return val

	@spend_last_year.setter
	def spend_last_year(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "spend_last_year", value)

	@property
	def insolvent_years(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("insolvent_years")
		val = getattr(sub, "insolvent_years", None)
		if val is None:
			raise AttributeError("insolvent_years")
		return val

	@insolvent_years.setter
	def insolvent_years(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "insolvent_years", value)

	@property
	def credit_frozen_until(self):
		return getattr(self.state.household, "credit_frozen_until")

	@credit_frozen_until.setter
	def credit_frozen_until(self, value):
		setattr(self.state.household, "credit_frozen_until", value)

	@property
	def bondage_debt(self):
		return getattr(self.state.household, "bondage_debt")

	@bondage_debt.setter
	def bondage_debt(self, value):
		setattr(self.state.household, "bondage_debt", value)

	@property
	def bondage_years_left(self):
		return getattr(self.state.household, "bondage_years_left")

	@bondage_years_left.setter
	def bondage_years_left(self, value):
		setattr(self.state.household, "bondage_years_left", value)

	@property
	def protection(self):
		return getattr(self.state.household, "protection")

	@protection.setter
	def protection(self, value):
		setattr(self.state.household, "protection", value)

	@property
	def reputation(self):
		return getattr(self.state.household, "reputation")

	@reputation.setter
	def reputation(self, value):
		setattr(self.state.household, "reputation", value)

	@property
	def eminence(self):
		return getattr(self.state.household, "eminence")

	@eminence.setter
	def eminence(self, value):
		setattr(self.state.household, "eminence", value)

	@property
	def scandal(self):
		return getattr(self.state.household, "scandal")

	@scandal.setter
	def scandal(self, value):
		setattr(self.state.household, "scandal", value)

	@property
	def scandal_last_year(self):
		return getattr(self.household, "scandal_last_year", None)

	@scandal_last_year.setter
	def scandal_last_year(self, value):
		setattr(self.household, "scandal_last_year", value)

	@property
	def artisans(self):
		return getattr(self.state.household, "artisans")

	@artisans.setter
	def artisans(self, value):
		setattr(self.state.household, "artisans", value)

	@property
	def scholars(self):
		return getattr(self.state.household, "scholars")

	@scholars.setter
	def scholars(self, value):
		setattr(self.state.household, "scholars", value)

	@property
	def employees(self):
		return getattr(self.state.household, "employees")

	@employees.setter
	def employees(self, value):
		setattr(self.state.household, "employees", value)

	@property
	def freedmen(self):
		return getattr(self.state.household, "freedmen")

	@freedmen.setter
	def freedmen(self, value):
		setattr(self.state.household, "freedmen", value)

	@property
	def slaves(self):
		return getattr(self.state.household, "slaves")

	@slaves.setter
	def slaves(self, value):
		setattr(self.state.household, "slaves", value)

	@property
	def manumitted_total(self):
		return getattr(self.state.household, "manumitted_total")

	@manumitted_total.setter
	def manumitted_total(self, value):
		setattr(self.state.household, "manumitted_total", value)

	@property
	def wages_earned(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("wages_earned")
		val = getattr(sub, "wages_earned", None)
		if val is None:
			raise AttributeError("wages_earned")
		return val

	@wages_earned.setter
	def wages_earned(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "wages_earned", value)

	@property
	def wages_prepaid(self):
		return getattr(self.state.household, "wages_prepaid")

	@wages_prepaid.setter
	def wages_prepaid(self, value):
		setattr(self.state.household, "wages_prepaid", value)

	@property
	def interest_paid(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("interest_paid")
		val = getattr(sub, "interest_paid", None)
		if val is None:
			raise AttributeError("interest_paid")
		return val

	@interest_paid.setter
	def interest_paid(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "interest_paid", value)

	@property
	def bounties_paid(self):
		return getattr(self.state.household, "bounties_paid")

	@bounties_paid.setter
	def bounties_paid(self, value):
		setattr(self.state.household, "bounties_paid", value)

	@property
	def directors_extra(self):
		return getattr(self.state.household, "directors_extra")

	@directors_extra.setter
	def directors_extra(self, value):
		setattr(self.state.household, "directors_extra", value)

	@property
	def contract_hours(self):
		return getattr(self.state.household, "contract_hours")

	@contract_hours.setter
	def contract_hours(self, value):
		setattr(self.state.household, "contract_hours", value)

	@property
	def worker_housing_places(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("worker_housing_places")
		val = getattr(sub, "worker_housing_places", None)
		if val is None:
			raise AttributeError("worker_housing_places")
		return val

	@worker_housing_places.setter
	def worker_housing_places(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "worker_housing_places", value)

	@property
	def trade_schools(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("trade_schools")
		val = getattr(sub, "trade_schools", None)
		if val is None:
			raise AttributeError("trade_schools")
		return val

	@trade_schools.setter
	def trade_schools(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "trade_schools", value)

	@property
	def trades_created(self):
		return getattr(self.state.household, "trades_created")

	@trades_created.setter
	def trades_created(self, value):
		setattr(self.state.household, "trades_created", value)

	@property
	def trades_endemic(self):
		return getattr(self.state.household, "trades_endemic")

	@trades_endemic.setter
	def trades_endemic(self, value):
		setattr(self.state.household, "trades_endemic", value)

	@property
	def trade_introduced_year(self):
		return getattr(self.state.household, "trade_introduced_year")

	@trade_introduced_year.setter
	def trade_introduced_year(self, value):
		setattr(self.state.household, "trade_introduced_year", value)

	@property
	def training(self):
		return getattr(self.state.household, "training")

	@training.setter
	def training(self, value):
		setattr(self.state.household, "training", value)

	@property
	def familiarity(self):
		return getattr(self.state.household, "familiarity")

	@familiarity.setter
	def familiarity(self, value):
		setattr(self.state.household, "familiarity", value)

	@property
	def last_taught(self):
		return getattr(self.state.household, "last_taught")

	@last_taught.setter
	def last_taught(self, value):
		setattr(self.state.household, "last_taught", value)

	@property
	def last_settlement(self):
		return getattr(self.state.household, "last_settlement")

	@last_settlement.setter
	def last_settlement(self, value):
		setattr(self.state.household, "last_settlement", value)

	@property
	def work_trade(self):
		return getattr(self.state.household, "work_trade")

	@work_trade.setter
	def work_trade(self, value):
		setattr(self.state.household, "work_trade", value)

	@property
	def log(self):
		return getattr(self.state.household, "log")

	@log.setter
	def log(self, value):
		setattr(self.state.household, "log", value)

	@property
	def _last_buy_refusal(self):
		return getattr(self.household, "_last_buy_refusal", None)

	@_last_buy_refusal.setter
	def _last_buy_refusal(self, value):
		setattr(self.household, "_last_buy_refusal", value)

	@property
	def _material_demand_cache(self):
		return getattr(self.household, "_material_demand_cache", None)

	@_material_demand_cache.setter
	def _material_demand_cache(self, value):
		setattr(self.household, "_material_demand_cache", value)

	@property
	def _said_stack_caution(self):
		return getattr(self.household, "_said_stack_caution", None)

	@_said_stack_caution.setter
	def _said_stack_caution(self, value):
		setattr(self.household, "_said_stack_caution", value)

	# =========================================================================
	# ProjectsState Compatibility Properties
	# =========================================================================

	@property
	def active(self):
		return getattr(self.state.projects, "active")

	@active.setter
	def active(self, value):
		setattr(self.state.projects, "active", value)

	@property
	def done(self):
		return getattr(self.state.projects, "done")

	@done.setter
	def done(self, value):
		setattr(self.state.projects, "done", value)

	@property
	def done_year(self):
		sub = getattr(self.state, "projects", None)
		if sub is None:
			raise AttributeError("done_year")
		val = getattr(sub, "done_year", None)
		if val is None:
			raise AttributeError("done_year")
		return val

	@done_year.setter
	def done_year(self, value):
		sub = getattr(self.state, "projects", None)
		if sub is not None:
			setattr(sub, "done_year", value)

	@property
	def revealed(self) -> Set[str]:
		return self.state.projects.revealed

	@revealed.setter
	def revealed(self, value: Iterable[str]) -> None:
		cur = self.state.projects.revealed
		self.state.projects.revealed = (set(value) if cur is None else set(cur) | set(value))

	@property
	def operating(self):
		return getattr(self.state.projects, "operating")

	@operating.setter
	def operating(self, value):
		setattr(self.state.projects, "operating", value)

	@property
	def mothballed(self):
		return getattr(self.state.projects, "mothballed")

	@mothballed.setter
	def mothballed(self, value):
		setattr(self.state.projects, "mothballed", value)

	@property
	def shut_for_staff(self):
		sub = getattr(self.state, "projects", None)
		if sub is None:
			raise AttributeError("shut_for_staff")
		val = getattr(sub, "shut_for_staff", None)
		if val is None:
			raise AttributeError("shut_for_staff")
		return val

	@shut_for_staff.setter
	def shut_for_staff(self, value):
		sub = getattr(self.state, "projects", None)
		if sub is not None:
			setattr(sub, "shut_for_staff", value)

	@property
	def bountied(self):
		return getattr(self.state.projects, "bountied")

	@bountied.setter
	def bountied(self, value):
		setattr(self.state.projects, "bountied", value)

	@property
	def granted(self):
		return getattr(self.state.projects, "granted")

	@granted.setter
	def granted(self, value):
		setattr(self.state.projects, "granted", value)

	@property
	def forgotten(self):
		return getattr(self.state.projects, "forgotten")

	@forgotten.setter
	def forgotten(self, value):
		setattr(self.state.projects, "forgotten", value)

	@property
	def failed_attempts(self):
		return getattr(self.state.projects, "failed_attempts")

	@failed_attempts.setter
	def failed_attempts(self, value):
		setattr(self.state.projects, "failed_attempts", value)

	@property
	def paid_towards(self):
		return getattr(self.state.projects, "paid_towards")

	@paid_towards.setter
	def paid_towards(self, value):
		setattr(self.state.projects, "paid_towards", value)

	@property
	def trade_hours_used(self):
		return getattr(self.state.projects, "trade_hours_used")

	@trade_hours_used.setter
	def trade_hours_used(self, value):
		setattr(self.state.projects, "trade_hours_used", value)

	# =========================================================================
	# EconomyState Compatibility Properties
	# =========================================================================

	@property
	def _dashboard_history(self):
		sub = getattr(self.state, "economy", None)
		if sub is None:
			raise AttributeError("_dashboard_history")
		val = getattr(sub, "_dashboard_history", None)
		if val is None:
			raise AttributeError("_dashboard_history")
		return val

	@_dashboard_history.setter
	def _dashboard_history(self, value):
		sub = getattr(self.state, "economy", None)
		if sub is not None:
			setattr(sub, "_dashboard_history", value)

	@property
	def binding(self):
		return getattr(self.state.economy, "binding")

	@binding.setter
	def binding(self, value):
		setattr(self.state.economy, "binding", value)

	@property
	def economy(self):
		return getattr(self.state.economy, "economy")

	@economy.setter
	def economy(self, value):
		setattr(self.state.economy, "economy", value)

	@property
	def farm_hectares(self):
		sub = getattr(self.state, "economy", None)
		if sub is None:
			raise AttributeError("farm_hectares")
		val = getattr(sub, "farm_hectares", None)
		if val is None:
			raise AttributeError("farm_hectares")
		return val

	@farm_hectares.setter
	def farm_hectares(self, value):
		sub = getattr(self.state, "economy", None)
		if sub is not None:
			setattr(sub, "farm_hectares", value)

	@property
	def farm_stock_kg(self):
		return getattr(self.state.economy, "farm_stock_kg")

	@farm_stock_kg.setter
	def farm_stock_kg(self, value):
		setattr(self.state.economy, "farm_stock_kg", value)

	@property
	def forest_ha(self):
		return getattr(self.state.economy, "forest_ha")

	@forest_ha.setter
	def forest_ha(self, value):
		setattr(self.state.economy, "forest_ha", value)

	@property
	def mine_tranches(self):
		sub = getattr(self.state, "economy", None)
		if sub is None:
			raise AttributeError("mine_tranches")
		val = getattr(sub, "mine_tranches", None)
		if val is None:
			raise AttributeError("mine_tranches")
		return val

	@mine_tranches.setter
	def mine_tranches(self, value):
		sub = getattr(self.state, "economy", None)
		if sub is not None:
			setattr(sub, "mine_tranches", value)

	@property
	def mines(self):
		return getattr(self.state.economy, "mines")

	@mines.setter
	def mines(self, value):
		setattr(self.state.economy, "mines", value)

	@property
	def money_real(self):
		return getattr(self.state.economy, "money_real")

	@money_real.setter
	def money_real(self, value):
		setattr(self.state.economy, "money_real", value)

	@property
	def nitre_bed_m2(self):
		return getattr(self.state.economy, "nitre_bed_m2")

	@nitre_bed_m2.setter
	def nitre_bed_m2(self, value):
		setattr(self.state.economy, "nitre_bed_m2", value)

	@property
	def output_factor(self):
		return getattr(self.state.economy, "output_factor")

	@output_factor.setter
	def output_factor(self, value):
		setattr(self.state.economy, "output_factor", value)

	@property
	def shortages(self):
		return getattr(self.state.economy, "shortages")

	@shortages.setter
	def shortages(self, value):
		setattr(self.state.economy, "shortages", value)

	@property
	def throttle(self):
		return getattr(self.state.economy, "throttle")

	@throttle.setter
	def throttle(self, value):
		setattr(self.state.economy, "throttle", value)

	# =========================================================================
	# GovernanceState Compatibility Properties
	# =========================================================================

	@property
	def inst_units(self):
		sub = getattr(self.state, "governance", None)
		if sub is None:
			raise AttributeError("inst_units")
		val = getattr(sub, "inst_units", None)
		if val is None:
			raise AttributeError("inst_units")
		return val

	@inst_units.setter
	def inst_units(self, value):
		sub = getattr(self.state, "governance", None)
		if sub is not None:
			setattr(sub, "inst_units", value)

	# =========================================================================
	# FounderState Compatibility Properties
	# =========================================================================

	@property
	def _founder_death_aged(self):
		sub = getattr(self.state, "founder", None)
		if sub is None:
			raise AttributeError("_founder_death_aged")
		val = getattr(sub, "_founder_death_aged", None)
		if val is None:
			raise AttributeError("_founder_death_aged")
		return val

	@_founder_death_aged.setter
	def _founder_death_aged(self, value):
		sub = getattr(self.state, "founder", None)
		if sub is not None:
			setattr(sub, "_founder_death_aged", value)

	@property
	def _founder_death_year(self):
		sub = getattr(self.state, "founder", None)
		if sub is None:
			raise AttributeError("_founder_death_year")
		val = getattr(sub, "_founder_death_year", None)
		if val is None:
			raise AttributeError("_founder_death_year")
		return val

	@_founder_death_year.setter
	def _founder_death_year(self, value):
		sub = getattr(self.state, "founder", None)
		if sub is not None:
			setattr(sub, "_founder_death_year", value)

	@property
	def dead_reason(self):
		return getattr(self.state.founder, "dead_reason")

	@dead_reason.setter
	def dead_reason(self, value):
		setattr(self.state.founder, "dead_reason", value)

	@property
	def founder_alive(self):
		return getattr(self.state.founder, "founder_alive")

	@founder_alive.setter
	def founder_alive(self, value):
		setattr(self.state.founder, "founder_alive", value)

	@property
	def life_left(self):
		return getattr(self.state.founder, "life_left")

	@life_left.setter
	def life_left(self, value):
		setattr(self.state.founder, "life_left", value)

	@property
	def policy(self):
		return getattr(self.state.founder, "policy")

	@policy.setter
	def policy(self, value):
		setattr(self.state.founder, "policy", value)

	# =========================================================================
	# ScenarioState Compatibility Properties
	# =========================================================================

	@property
	def _said_command_index(self):
		sub = getattr(self.state, "scenario", None)
		if sub is None:
			raise AttributeError("_said_command_index")
		val = getattr(sub, "_said_command_index", None)
		if val is None:
			raise AttributeError("_said_command_index")
		return val

	@_said_command_index.setter
	def _said_command_index(self, value):
		sub = getattr(self.state, "scenario", None)
		if sub is not None:
			setattr(sub, "_said_command_index", value)

	@property
	def _said_parallelism(self):
		sub = getattr(self.state, "scenario", None)
		if sub is None:
			raise AttributeError("_said_parallelism")
		val = getattr(sub, "_said_parallelism", None)
		if val is None:
			raise AttributeError("_said_parallelism")
		return val

	@_said_parallelism.setter
	def _said_parallelism(self, value):
		sub = getattr(self.state, "scenario", None)
		if sub is not None:
			setattr(sub, "_said_parallelism", value)

	@property
	def _said_scandal(self):
		sub = getattr(self.state, "scenario", None)
		if sub is None:
			raise AttributeError("_said_scandal")
		val = getattr(sub, "_said_scandal", None)
		if val is None:
			raise AttributeError("_said_scandal")
		return val

	@_said_scandal.setter
	def _said_scandal(self, value):
		sub = getattr(self.state, "scenario", None)
		if sub is not None:
			setattr(sub, "_said_scandal", value)

	@property
	def goal_year(self):
		return getattr(self.state.scenario, "goal_year")

	@goal_year.setter
	def goal_year(self, value):
		setattr(self.state.scenario, "goal_year", value)

	@property
	def year(self):
		return getattr(self.state.scenario, "year")

	@year.setter
	def year(self, value):
		setattr(self.state.scenario, "year", value)

	@property
	def fog(self):
		return self.state._fog

	@fog.setter
	def fog(self, value):
		self.state._fog = bool(value)

	@property
	def goal(self):
		return self.state._goal

	@goal.setter
	def goal(self, value):
		self.state._goal = value

	# =========================================================================
	# PopulationState Compatibility Properties
	# =========================================================================

	@property
	def _food_pop_bonus_applied(self):
		sub = getattr(self.state, "population", None)
		if sub is None:
			raise AttributeError("_food_pop_bonus_applied")
		val = getattr(sub, "_food_pop_bonus_applied", None)
		if val is None:
			raise AttributeError("_food_pop_bonus_applied")
		return val

	@_food_pop_bonus_applied.setter
	def _food_pop_bonus_applied(self, value):
		sub = getattr(self.state, "population", None)
		if sub is not None:
			setattr(sub, "_food_pop_bonus_applied", value)

	@property
	def pop_children(self):
		return self.population.children

	@pop_children.setter
	def pop_children(self, value):
		val = float(value)
		self.population.children = val
		if hasattr(self, "state") and self.state is not None and self.state.population is not None:
			self.state.population.pop_children = val

	@property
	def pop_working_age(self):
		return self.population.working_age

	@pop_working_age.setter
	def pop_working_age(self, value):
		val = float(value)
		self.population.working_age = val
		if hasattr(self, "state") and self.state is not None and self.state.population is not None:
			self.state.population.pop_working_age = val

	@property
	def pop_elderly(self):
		return self.population.elderly

	@pop_elderly.setter
	def pop_elderly(self, value):
		val = float(value)
		self.population.elderly = val
		if hasattr(self, "state") and self.state is not None and self.state.population is not None:
			self.state.population.pop_elderly = val


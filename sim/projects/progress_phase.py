"""The yearly project-progress step: hours, bills, affordability and finishing.

Each project in hand takes its turn in priority order: is there anybody to do the work, how many hours it gets, what
labour and bill follow from that, whether the household can afford the bill, then the bookkeeping and the completion
check. Every random draw the stages make (completion rolls the dice once per attempt) runs once, in this order, for each
project."""
from sim.agents.api import edges
from sim.ledger.api import NoteSpend, PayEdge
from sim.materials.api import ApplyThrottle
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent
from sim.workforce.api import ResetTradeHours, SpendDirectorHours

from . import funding as project_funding, start_rules
from .arrears_hours_line import arrears_hours_line
from .hour_offer import hours_offered, unmet_directive_cause
from .needed_commands import NoteYearSpend


class ProgressPhase:
	def apply_advance_projects(self, command):
		"""The year's progress step for the acting seat: (hours left in the pool, the same before wage work, the hours
		the projects effectively used)."""
		return self._step_progress(command.pool, command.hired_left)

	def _step_progress_project(self, node_id, pool_rank, pool_total_this_year, pool_active_count_this_year, remaining,
	                           hired_left, arrears_hours_lost, directed_hours_unused, _afford_context=None):
		# One project's share of this year's director hours and money. Threads remaining/hired_left through by argument
		# and return, the same shared pool every project in the loop draws from in order; arrears_hours_lost and
		# directed_hours_unused are the two logging lists _step_progress() reports from once, after every project has
		# had its turn.
		needs = self.needs
		project_state = needs.legacy_projects().active[node_id]
		node = needs.tree_nodes()[node_id]
		project_state["pool_total_this_year"] = pool_total_this_year
		project_state["pool_active_count_this_year"] = pool_active_count_this_year
		project_state["pool_rank_this_year"] = pool_rank
		project_state["pool_remaining_before_this_year"] = round(remaining, 1)
		# A PIPELINE, ONE STAGE PER CONCERN, IN A FIXED ORDER: is there anybody to do the work, how many hours does the
		# project get this year, what labour and bill follow from that, can the household afford the bill, then the
		# bookkeeping and completion check. Every dice-touching call these stages make runs exactly once, in exactly this
		# order, for exactly this project: the stages are called unconditionally in sequence, and only the two early
		# returns below skip any of them.
		if self._project_progress_trade_gate(node_id, project_state, node):
			return remaining, hired_left, 0.0
		remaining, per, spent_hours, _dir_hours = self._project_progress_offer_hours(
			node_id, project_state, remaining, pool_total_this_year, directed_hours_unused)
		_labour = self._project_progress_labour_and_bill(node_id, project_state, node, hired_left, per, spent_hours)
		if _labour is None:
			return remaining, hired_left, 0.0
		hired_left, money, refunded = _labour
		money, refunded = self._project_progress_afford_gate(
			node_id, project_state, money, refunded, spent_hours, per, arrears_hours_lost, _afford_context=_afford_context)
		self._project_progress_finish(
			node_id, project_state, money, refunded, spent_hours, _dir_hours, directed_hours_unused,
			_afford_context=_afford_context)
		return remaining, hired_left, project_state["hours_effective_this_year"]

	def _project_progress_trade_gate(self, node_id, project_state, node):
		# Stage 1: is there anybody to do the work. Returns True when the project is stalled or just halted this year, in
		# which case the caller returns immediately with no hours or money spent. Returns False, and clears
		# stalled_years, when the project can proceed.
		#
		# IS THERE ANYBODY TO DO THE WORK? If a trade this project needs has vanished since it started (the machinists you
		# taught died out, say), nothing can be done on it this year, and your own hours should go somewhere they are
		# useful rather than into a project that cannot absorb them. Without it a project whose trade had disappeared sat
		# in `active` for ever: hours went in, no money was spent because no work was done, so the bill was never paid, so
		# it could never complete, so it never released the slot.
		#
		# ONLY A TRADE THIS PROJECT STILL OWES SOMETHING TO: checked against `lab_left` (how much of each trade's hours
		# remain to be drawn), NOT the node's ORIGINAL total (`want > 0`), which never goes back to zero no matter how much
		# of that trade's hours the project has already drawn.
		needs = self.needs
		_lab_left = project_state.get("lab_left")
		if _lab_left is None:
			_lab_left = node["lab"]
		blocked = [trade_id for trade_id, want in node["lab"].items()
		           if want > 0 and _lab_left.get(trade_id, want) > 0
		           and needs.market_supply[trade_id] <= 0.0]
		if blocked:
			projects = needs.legacy_projects()
			project_state["stalled_years"] = project_state.get("stalled_years", 0) + 1
			project_state["blocked_on_trades"] = blocked
			if project_state["stalled_years"] >= start_rules.STALL_YEARS_BEFORE_ABANDONMENT:
				needs.send(RecordEvent.of("project_halted_no_labour", "HALTED %s: there is nobody here who can "
				           "do this work (%s). What you spent is lost"
				           % (node_id, ", ".join(blocked[:2]))))
				projects.active.pop(node_id, None)
				projects.bountied.discard(node_id)
			else:
				# WARN BEFORE THE MONEY GOES: a countdown to abandonment running silently, with nothing said until
				# everything spent is taken at once, gives no chance to act. Say it each year, with the number of years
				# left and what would fix it.
				_left = start_rules.STALL_YEARS_BEFORE_ABANDONMENT - project_state["stalled_years"]
				needs.send(RecordEvent.of("project_cannot_go_on", "%s cannot go on: no %s here. It has "
				           "%d year%s before it is abandoned and "
				           "what you spent on it is lost. Teach "
				           "the trade, or 'stop %s' now and keep "
				           "your hours"
				           % (node_id, " or ".join(blocked[:2]), _left,
				              "" if _left == 1 else "s", node_id), project=node_id, trades=list(blocked), years_left=_left))
				# Nothing happened here this year - say so, rather than leaving last year's hours_offered/effective
				# sitting on the entry looking like they still applied.
				project_state["hours_offered_this_year"] = 0.0
				project_state["hours_effective_this_year"] = 0.0
			return True
		project_state["stalled_years"] = 0
		return False

	def _project_progress_offer_hours(self, node_id, project_state, remaining, pool_total_this_year, directed_hours_unused):
		# Stage 2: how many hours the project gets this year (`per`), what that leaves of the shared pool (`remaining`),
		# and the first of the two places a standing allocation can go unhonoured. Returns the updated remaining, per,
		# spent_hours (for the give-backs later stages compute) and _dir_hours (read again by stage 5's inner-gap check).
		#
		# project_hour_pace is the formula `work`'s own pre-sale warning reads too, so a warning about starving an
		# active project can never disagree with what this loop actually offers it.
		#
		# A STANDING ALLOCATION IS A CEILING, NOT A FLOOR: the allocation is only ever a THIRD candidate in the min() -
		# never a reason to offer MORE than remaining or the project's own pace would otherwise allow - so a directed
		# project can still never outrun the pool it shares with everything else, and never get hours faster than its
		# own calendar floor could ever use. What it changes is ORDER and that an undirected project never crowds this
		# one out of the share the player asked for it to have.
		needs = self.needs
		_dir_hours = needs.hour_commitments()["allocations"].get(node_id)
		_pace_cap = self.project_hour_pace(node_id)
		_project_throttle = needs.send(ApplyThrottle(node_id))
		per = hours_offered(remaining, _pace_cap, _dir_hours, _project_throttle)
		remaining -= per
		# WHAT WAS ACTUALLY TAKEN OFF, which is not the same as what was offered: `per` is allowed to exceed ph_left (the
		# pace offers a full year's worth even to a project with an hour to run), and the subtraction clamps at zero. A
		# refund computed from `per` instead of from what was truly spent could hand back more than was ever taken. You
		# cannot be refunded work you never did.
		spent_hours = min(per, project_state["ph_left"])
		project_state["ph_left"] = max(0.0, project_state["ph_left"] - per)
		needs.send(SpendDirectorHours(per if needs.founder()["alive"] else 0))
		# Hours OFFERED this year vs hours that actually did anything. `refunded` tracks the difference: hours credited
		# back to ph_left below because a trade or the money to pay for it fell short. This must stay visible to the
		# player: showing only the net hours left reads as confusing when half a year's hours come back with no
		# explanation of why.
		project_state["hours_offered_this_year"] = round(per, 1)
		# WHAT THE PLAYER ACTUALLY ASKED FOR, READ BACK AT THE END OF THE YEAR - `portfolio` and `why` print this field
		# verbatim: never recompute a number a player is told, always read the one this loop actually used.
		project_state["hours_directed_this_year"] = (round(_dir_hours, 1) if _dir_hours else None)
		# SAY SO WHEN THE PROMISE ITSELF WAS NOT KEPT, before any trade or money shortfall even has a chance to bite
		# further in. A directive can be cut short right here, two ways: the POOL had already given the rest away, or this
		# project's OWN pace - what is left to do, or its calendar floor - could not use that many hours even with the
		# whole pool behind it. Either is a real, nameable reason; "it disappeared" is not.
		_unmet = unmet_directive_cause(_dir_hours, per, _pace_cap, _project_throttle, needs.material_binding())
		if _unmet == "shortage_throttle":
			directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
			    Refusal("shortage_throttle", "a shortage of %s has every project (this one "
			            "included) running at %d%% of the pace its "
			            "hours alone would allow"
			            % (needs.material_binding(), round(_project_throttle * 100)))))
		elif _unmet == "own_pace":
			directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
			    Refusal("own_pace", "its own pace this year - at most %s hours, set "
			            "by how much of it is left to do or its "
			            "calendar floor, not by your hours - could not "
			            "use the rest" % needs.plain_number(_pace_cap * _project_throttle))))
		elif _unmet == "pool_claimed":
			directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
			    Refusal("pool_claimed", "your other standing allocations and active "
			            "work already claimed the rest of this year's "
			            "%s hours before this one's turn came ('priority "
			            "<id> first' moves a project up the queue)"
			            % needs.plain_number(pool_total_this_year))))
		return remaining, per, spent_hours, _dir_hours

	def _project_progress_labour_and_bill(self, node_id, project_state, node, hired_left, per, spent_hours):
		# Stage 3: the labour this project can actually hire this year and the bill that follows from it. Returns None
		# when the project was abandoned this year, in which case the caller returns immediately. Otherwise returns the
		# updated hired_left, money and refunded.
		needs = self.needs
		refunded = 0.0
		project_state["yrs"] += 1
		frac = min(1.0, 1.0 / max(1.0, node["yrs"]))
		# Diagnostic callers can construct active-project dictionaries directly, so initialise an omitted bill defensively.
		if project_state.get("cost_left") is None:
			project_state["cost_left"] = max(0.0, needs.project_cost(node_id) - project_state["spent"])
		# LABOUR BY TRADE, HOURS A TOTAL AND A CEILING: what binds is the scarcest trade this project actually needs
		# (see lab_year_draw); this call site only has to act on what it returns.
		hired_hours, worst, frac, _abandon = self.lab_year_draw(node_id, project_state, frac, hired_left)
		if _abandon:
			projects = needs.legacy_projects()
			needs.send(RecordEvent.of("project_abandoned", "ABANDONED %s: %s" % (node_id, _abandon)))
			projects.active.pop(node_id, None)
			projects.bountied.discard(node_id)
			return None
		if worst < 1.0:
			# NEVER ALL OF IT: the refund says "hours offered but not usable, because the trade was booked", and with no
			# floor under it could hand back every hour that had actually gone in. If a fraction `worst` of the work could
			# be done, then a fraction `worst` of it WAS done, and that much can never be given back. Progress is strictly
			# positive whenever anybody at all can be found.
			give_back = min(spent_hours - refunded, per * 0.4 * (1.0 - worst), spent_hours * (1.0 - worst))
			project_state["ph_left"] += max(0.0, give_back)
			refunded += max(0.0, give_back)
		if hired_hours > hired_left:
			frac *= hired_left / max(hired_hours, 1e-9)
			hired_hours = hired_left
		# THE INSTALMENT IS WHAT A CONSTRAINED YEAR CAN DO; THE BILL IS WHAT IS LEFT: working from the already-scaled
		# `frac`, applied directly to `cost_left`, means a shortage sets how FAST a project can be paid off and never
		# stops the last payment landing. Working the payment out first and then multiplying it by each shortage in turn
		# would instead pay a FRACTION OF WHAT WAS LEFT every year, forever, once the remaining balance is smaller than a
		# year's instalment - a geometric decay that approaches zero and never reaches it, while completion needs the
		# bill down to half a denarius.
		money = project_funding.year_bill(project_state["cost_left"], needs.project_cost(node_id), frac)
		hired_left -= hired_hours
		return hired_left, money, refunded

	def _project_progress_afford_gate(self, node_id, project_state, money, refunded, spent_hours, per, arrears_hours_lost,
	                                  _afford_context=None):
		# Stage 4: can the household actually afford this year's bill. Returns the updated money and refunded.
		# You may spend into debt, up to what someone will lend you, and no further. Beyond that the work simply does not
		# get paid for this year, and a year nobody was paid for is a year of little progress. What must NOT happen is the
		# bill being forgiven.
		#
		# The margin is deliberate. Spending to the last denarius of your credit means next year's rent breaches the limit
		# and the creditors halt every project you have. Reserve next year's fixed costs AND most of the credit line.
		# Reserve only the SHORTFALL, not the whole running cost: this year's rent and wages have already been taken out
		# of capital at the top of the year.
		needs = self.needs
		if _afford_context is not None:
			revenue = _afford_context["revenue"]
			upkeep = _afford_context["upkeep"]
			mine_operating = _afford_context["mine_operating"]
		else:
			revenue = needs.revenue_estimate()
			upkeep = needs.upkeep()
			mine_operating = needs.mine_operating_cost()
		fixed = (
			needs.living_cost(revenue, upkeep, None)
			+ upkeep
			+ mine_operating
		)
		capital = needs.acting_balance()
		purse = project_funding.project_purse(capital, needs.credit_limit(revenue, upkeep, None), fixed, revenue)
		# A project with nothing left to pay asks for no money, so a purse gone negative from arrears that are not its own
		# does not stop it making calendar-waiting progress (fund_year).
		funding = project_funding.fund_year(money, purse, spent_hours, refunded, per, capital < 0)
		if funding.underfunded:
			project_state["ph_left"] += funding.gave_back
			project_state["underfunded_this_year"] = True
			project_state["why_underfunded"] = funding.why
			# The founder-hours lost to arrears never come back; they are logged once after the loop.
			if funding.hours_lost_to_arrears:
				arrears_hours_lost.append((node_id, round(funding.hours_lost_to_arrears, 0)))
		else:
			project_state.pop("underfunded_this_year", None)
			project_state.pop("why_underfunded", None)
		money, refunded = funding.money, funding.refunded
		return money, refunded

	def _project_progress_finish(self, node_id, project_state, money, refunded, spent_hours, _dir_hours,
	                             directed_hours_unused, _afford_context=None):
		# Stage 5: spend the money, record the hours actually done, the second place a standing allocation can go
		# unhonoured, and the completion check. Nothing to return - project_state carries every result.
		needs = self.needs
		needs.send(PayEdge(edges.EDGE_SUPPLIERS, money, "project payments"))
		needs.send(NoteSpend(money))
		project_state["spent"] += money
		project_state["cost_left"] = max(0.0, project_state["cost_left"] - money)
		# spent_hours, NOT per. `per` is what was OFFERED, and it is allowed to exceed the hours the project actually had
		# left; the refunds above are capped at spent_hours for exactly that reason. Work reported that provably did not
		# happen would be about the one resource the whole game is built on.
		project_state["hours_effective_this_year"] = round(max(0.0, spent_hours - refunded), 1)
		# THE SECOND WAY A DIRECTIVE GOES UNHONOURED: OFFERED, THEN HANDED BACK. Unlike the check in stage 2, it must NOT
		# fire just because spent_hours fell short of `per` - a project a few hours from finished is offered a whole year's
		# pace and only needs a sliver of it, which is the project ending. Gated on why_underfunded/short_of_trade actually
		# being SET this year, so this can only ever name a real shortfall.
		if _dir_hours and _dir_hours > 0:
			_inner_gap = project_state["hours_offered_this_year"] - project_state["hours_effective_this_year"]
			# DEEP ARREARS ALREADY GETS ITS OWN LINE - "IN ARREARS: ... did almost nothing this year" - the sharper warning
			# of the two; this fires only for the money-short case arrears does NOT already cover.
			if _inner_gap > 1.0 and project_state.get("why_underfunded") and needs.acting_balance() >= 0:
				directed_hours_unused.append((node_id, round(_inner_gap, 0), project_state["why_underfunded"]))
			elif _inner_gap > 1.0 and project_state.get("short_of_trade"):
				directed_hours_unused.append((node_id, round(_inner_gap, 0), self.trade_shortfall_note(project_state)))
		# Count it HERE, after the hired-hours scaling and the affordability clamp, not before them: accumulating the
		# notional figure instead would make the year's project spend disagree with the actual capital movement.
		needs.send(NoteYearSpend(money))
		# calendar_floor, NOT a second copy of this formula - expected_calendar_years needs the identical figure to
		# project retries honestly.
		floor = self.calendar_floor(node_id)
		# THE BILL HAS TO BE PAID. Hours done and years elapsed are not enough; if the money never arrived, the thing was
		# never built.
		# HALF AN HOUR IS NOTHING LEFT TO DO: the give-back hands back a fraction of what was offered, so on a throttled
		# project ph_left decays geometrically towards zero and never exactly reaches it. The bill already has this exact
		# fix (cost_left <= 0.5 on the same line); hours need it too.
		if project_state["ph_left"] < 0.5:
			project_state["ph_left"] = 0.0
		if project_state["ph_left"] <= 0 and project_state["yrs"] >= floor:
			self.settle_cost_tail(node_id, project_state)
		if project_state["ph_left"] <= 0 and project_state["yrs"] >= floor and project_state["cost_left"] <= 0.5:
			self._complete(node_id)
			if _afford_context is not None:
				_afford_context["revenue"] = needs.revenue_estimate()
				_afford_context["upkeep"] = needs.upkeep()
		elif project_state["ph_left"] <= 0 and project_state["yrs"] >= floor and project_state["cost_left"] > 0.5:
			project_state["waiting_on_money"] = True

	def _step_progress(self, pool, hired_left):
		# 5. progress. Director hours go to the HIGHEST-PRIORITY active projects first, not spread evenly: a director who
		#    gives every project equal attention finishes nothing, which is a real failure mode but not the one we are
		#    trying to model here.
		needs = self.needs
		active_sorted = self.hour_priority_queue()
		remaining = pool
		needs.send(ResetTradeHours())
		# Summed as the loop runs, not re-read from the active record afterwards, because a project that completes THIS
		# year is popped from it before we would get to it.
		hours_effective_total = 0.0
		# NAMED, NOT JUST STORED ON THE PROJECT: `why_underfunded` answers "why is this stalled" only when a player thinks
		# to ask `why` or `portfolio`, which is not the same as announcing it. Founder-hours are the one resource that
		# never banks: a year of them lost to arrears and never announced is the least fair thing a status screen can
		# leave out. Collected here and logged once, after the loop, so a step that starves three projects at once gets
		# one clear line, not three.
		_arrears_hours_lost = []
		# AN ALLOCATION THE PLAYER EXPLICITLY ASKED FOR, AND DID NOT GET: hour_allocations is a promise the player made
		# about their OWN one resource that never banks; silently handing back less than it asked for - because the
		# project's own pace, its trade, or its money was the real ceiling, not the founder's hours - is the same
		# unfairness the arrears line exists to stop. Collected per project, and logged once below.
		_directed_hours_unused = []
		# WHY A PROJECT IS GETTING THE SHARE IT IS GETTING, STORED HERE AND NOWHERE ELSE: the only honest way to explain a
		# project's share of this year's directed hours is to read the numbers this loop actually used, never to guess at
		# them again from outside. `portfolio` reads these fields back verbatim.
		_pool_total_this_year = pool
		_pool_active_count_this_year = len(active_sorted)
		_afford_context = {
			"revenue": needs.revenue_estimate(),
			"upkeep": needs.upkeep(),
			"mine_operating": needs.mine_operating_cost(),
		}
		for _pool_rank, node_id in enumerate(active_sorted, start=1):
			remaining, hired_left, _effective = self._step_progress_project(
				node_id, _pool_rank, _pool_total_this_year, _pool_active_count_this_year,
				remaining, hired_left, _arrears_hours_lost, _directed_hours_unused,
				_afford_context=_afford_context)
			hours_effective_total += _effective
		# ARREARS COSTS YOU THE YEAR'S HOURS, NOT JUST THE MONEY - SAY SO. Named per project, so 'why <id>' and this line
		# never disagree about which project or how much.
		if _arrears_hours_lost:
			needs.send(RecordEvent.from_line(arrears_hours_line(_arrears_hours_lost, needs.plain_number)))  # plain line: arrears_hours_line builds the LogLine and its kind
		# A STANDING ALLOCATION THE PLAYER GAVE, AND DID NOT GET - SAID, NOT LEFT FOR THEM TO NOTICE. Sorted by id for a
		# deterministic order across runs with the same seed - several projects can be cut short in the same year.
		self.report_unused_directed_hours(_directed_hours_unused)
		# Snapshot BEFORE 5b spends more of `remaining` on wage work: otherwise offered_to_projects below double-counts
		# wage hours as though they had been offered to projects too, since 5b draws from the same pool.
		remaining_after_projects = remaining
		return remaining, remaining_after_projects, hours_effective_total

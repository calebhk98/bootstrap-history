"""What the seat does about its people before it starts new projects: teach the trades the society has lost, and sell the
hours a standing `work` order asks for. Runs as the `seat_prelude` phase."""
from sim.reporting.api import RecordEvent

from .constants import RETEACH_EVERY
from .reteach_rules import PROJECT_IN_HAND_SCORE, past_cooldown, teaching_budget, trade_is_gone
from .rules import work_order_shortfall


class Prelude:

	def step_prelude(self, seat_id=None):
		self.step_teach_trades()              # 4a. teach the trades this society does not have
		self.step_standing_work_directive()   # 4a(ii). the standing "work" directive

	def hours_report_is_news(self, key, signature):
		"""True the first time a standing order falls short this way, False while it repeats."""
		reported = self.seat.unused_hours_reported
		if reported.get(key) == signature:
			return False
		reported[key] = signature
		return True

	def clear_hours_report(self, key):
		self.seat.unused_hours_reported.pop(key, None)

	def step_teach_trades(self):
		# 4a2. TEACH THE TRADES THIS SOCIETY DOES NOT HAVE. The optimizer has to
		#      do this for itself or half the tree is unreachable; a player does
		#      it with `train`, or turns this on.
		if self.needs.founder()["policy"].get("auto_train", not self.needs.automation()["manual"]):
			workforce = self.seat
			done_nodes, active_nodes = self.needs.techniques_held(), self.needs.active_projects()
			nodes = self.needs.tree_nodes()
			year = self.needs.year()
			want = {}
			# LOCAL, PER-YEAR MEMO for market_supply()/trade_available().
			# Both are pure functions of staff and trades_created, which this
			# whole block only READS - train(), below, adds to trades_created,
			# but that happens once, at the very end, after every use of these
			# memos - so the same handful of distinct trade names (maybe
			# thirty) get recomputed from scratch once per NODE that lists
			# them in `lab`, and hundreds of nodes across the tree share the
			# same absent trade (machinist, engineer, ...). This dict is a
			# plain local, created fresh every call and discarded when the
			# block ends, so it needs no invalidation logic at all: nothing
			# outside this block ever reads it, so it cannot go stale.
			_ms_memo, _ta_memo = {}, {}

			def _market_supply(trade):
				value = _ms_memo.get(trade)
				if value is None:
					value = _ms_memo[trade] = self.labour.market_supply(trade)
				return value

			def _trade_avail(trade):
				value = _ta_memo.get(trade)
				if value is None:
					value = _ta_memo[trade] = self.labour.trade_available(trade)
				return value
			# Anything already in hand that has lost its trade comes FIRST: those
			# projects are burning a slot and will be halted if nobody turns up.
			for node_id in sorted(active_nodes):
				for trade_id in nodes[node_id]["lab"]:
					if _market_supply(trade_id) <= 0.0:
						want[trade_id] = want.get(trade_id, 0) + PROJECT_IN_HAND_SCORE
			# WORK THE PLAYER COULD START TODAY, not the whole tree. The old
			# test was "direct prerequisites satisfied", which is not "wanted":
			# it looked past cost, staff, state approval and every OTHER trade
			# a node needs, so it walked deep into the order training engineers,
			# then chemists, machinists and opticians, with no active project
			# asking for any of them. Its own description promises "when a
			# project needs them", and a project three tiers away with money
			# you do not have is not a project you need anything for yet.
			# ignore_trade asks the one question that answers that: if this
			# trade existed, would everything ELSE already let it start?
			# EXISTING IS NOT THE SAME AS ANYBODY BEING LEFT. A trade you
			# taught stays "available" for ever, so once the last machinist
			# had died of old age this loop skipped every node that needed
			# one and nobody was ever taught again. A Rome run built 829
			# technologies, sat on 31.9M denarii, and could not begin
			# precision_three_plate - which gates master_screw, the screw
			# lathe and the entire precision branch, ninety-nine of the
			# hundred and forty-six nodes on the road to the goal. This is
			# the same distinction start_reason learned an hour earlier.
			# _is_gone(trade) is memoized (_gone_memo) for the same reason
			# _market_supply/_trade_avail are: it reads only _trade_avail(trade),
			# _market_supply(trade) and the trade's pending headcount, which
			# read only the training queue and the employees - neither
			# mutated anywhere in this block; train(), at the very end of it,
			# is the only thing that changes either. `order` has ~2,800 nodes,
			# many naming the same handful of distinct trades, so each trade's
			# verdict is computed once and reused for every later node that
			# names it.
			_gone_memo = {}

			def _is_gone(trade):
				value = _gone_memo.get(trade)
				if value is None:
					value = _gone_memo[trade] = trade_is_gone(
						_trade_avail(trade), _market_supply(trade), self.labour.trade_headcount_pending(trade))
				return value
			for node_id in self.needs.project_order():
				if node_id in done_nodes or node_id in active_nodes:
					continue
				node = nodes[node_id]
				if not any(_is_gone(trade_id) for trade_id in node["lab"]):
					continue
				if not self.needs.start_check(node_id, True, None, False)[0]:
					continue
				for trade_id in node["lab"]:
					if _is_gone(trade_id):
						want[trade_id] = want.get(trade_id, 0) + 1
			# NOT EVERY YEAR: teaching two of a trade costs about nine hundred
			# of the founder's two thousand hours plus their keep, so
			# re-teaching a lost trade every single year it qualifies would
			# turn into a teaching treadmill that eats most of a run's
			# output. A trade is worth restoring; it is not worth half of
			# every year for ever.
			_taught = workforce.last_taught
			want = past_cooldown(want, _taught, year, RETEACH_EVERY)
			# AND ONLY IF YOU CAN PAY THEM: train() checks hours, literacy and
			# household room but nothing here about money, so teaching a
			# trade a household cannot actually afford to keep paid turns
			# every year after into a wage bill that eats its whole income.
			# A trade you cannot pay for is not a trade you have; it is a
			# wage bill that stops you building anything.
			#
			# Two standards, because the two cases are not alike. A trade a
			# project ALREADY IN HAND is waiting on (scored 500 above) is worth
			# borrowing against: that work is paid for and stops without it.
			# A trade for something you might start one day has to come out of
			# what you are actually clearing.
			_tr_rev = self.needs.revenue_estimate()
			_tr_upkeep = self.needs.upkeep()
			_spare_tr = _tr_rev - _tr_upkeep - self.needs.living_cost(_tr_rev, _tr_upkeep)
			for trade_id, _score in sorted(want.items(), key=lambda kv: (-kv[1], kv[0]))[:1]:
				_wages = 2.0 * self.labour.market.quote_annual(trade_id)
				_budget = teaching_budget(_score, _spare_tr, self.needs.acting_balance())
				if _wages > _budget:
					continue
				_first = trade_id not in workforce.trades_created
				taught, _msg = self.labour.train(trade_id, 2)
				# THE COOLDOWN IS ON TEACHING, NOT ON TRYING. Recording the
				# attempt meant a refusal - no room in the household, no hours
				# left, nobody to teach from - burned the trade's whole
				# twenty-five years, so the run went on needing machinists and
				# never asked again.
				if taught:
					_taught[trade_id] = year
					self.needs.send(RecordEvent.of("teaching_begun", "you begin teaching the first %ss this "
					                               "world has ever had" % trade_id if _first else
					                               "the last %ss are gone; you begin teaching "
					                               "more" % trade_id))

	def step_standing_work_directive(self):
		# 4a(ii). THE STANDING "WORK" DIRECTIVE. `work` (protocol.py) sells
		# hours for wages the moment a player types it; `allocate` lets them
		# say "sell N hours a year this way" ONCE and have it happen every
		# year without retyping it, the same standing-instruction idea as
		# the project directives just below. Run BEFORE `pool` is struck so
		# director_hours_committed() (which counts wage hours already sold
		# this year) sees it, exactly as it would if the player had typed
		# `work` by hand a moment ago.
		#
		# TOPPED UP, NOT DOUBLED. A player who already called `work` by hand
		# earlier this same turn has already sold some of the hours this
		# directive wants; this only sells the remainder, never the whole
		# directive again on top of what was already sold.
		workforce = self.seat
		_wd = workforce.hour_allocations.get("work")
		if _wd and _wd > 0 and workforce.work_trade:
			_already = workforce.wage_hours_this_year
			_want = work_order_shortfall(_wd, _already)
			if _want > 0.5:
				_room = max(0.0, self.labour.director_pool() - self.labour.director_hours_committed())
				_take = min(_want, _room)
				_got = 0.0
				if _take > 0.5:
					_pay, _werr = self.labour.work_for_wages(workforce.work_trade, _take)
					# pay > 0 with an error is a WARNING (a bad trade, or
					# starving an active project of its last hours), not a
					# refusal - see work_for_wages's own docstring. The sale
					# happened either way; only a genuine refusal (pay <= 0)
					# means none of it landed.
					if _pay > 0 or not _werr:
						_got = _take
				# SAY SO, THE SAME WAY AN UNHONOURED PROJECT DIRECTIVE DOES,
				# BELOW. A standing instruction nobody is told failed is the
				# same unfairness either way: the founder-hours it asked for
				# either went unsold or went somewhere the player never
				# chose.
				_work_reason = ("room" if _room < _want else "market")
				if _wd - (_already + _got) <= 1.0:
					self.clear_hours_report("work")
				elif self.hours_report_is_news("work", [round(_wd), _work_reason]):
					self.needs.send(RecordEvent.of("directed_hours_unused", "DIRECTED HOURS UNUSED: your standing "
						"order to sell %s hours a year as a "
						"%s only managed %s this year - %s. "
						"'allocate' changes or clears it"
						% (self.needs.plain_number(_wd), workforce.work_trade,
						   self.needs.plain_number(_already + _got),
						   "no more of your own hours were left "
						   "to sell once your projects and "
						   "training had theirs"
						   if _room < _want else
						   "nobody here will pay for that trade "
						   "any longer"), trade=workforce.work_trade, reason="no_hours_left" if _room < _want else "nobody_pays"))

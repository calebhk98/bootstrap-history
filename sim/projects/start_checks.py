"""Whether you may begin: the legality test a project must pass, check by check, in the order the contract fixes.

`start_check` is the legality test that explains a refusal; with `why` false it is the optimizer's inner loop, which
calls it for every node in the tree, so no sentence is built then (several are themselves built by walking the tree,
through `visibility`, which calls back into this test on each missing prerequisite). Each check returns None ("no
verdict, ask the next check") or the (ok, message) this test should return right now, so the FIRST check with an
opinion wins. The order of `START_CHECKS` (blocker_rules.py) is the contract."""
from typing import Any, Dict, Optional, Tuple

from sim.agents.api import research_gate
from sim.refusal import Refusal

from . import constants, funding, start_money, start_rules
from .blocker_rules import START_CHECKS, StartCheck
from .staff_gate import craftsmen_gate_text, scholar_gate_text
from .training_words import training_advice_text

Verdict = Optional[Tuple[bool, Any]]

SOCIAL_CATEGORIES = ("social", "institution", "foundation", "capability", "material")


class StartChecks:
	START_CHECKS = START_CHECKS

	def _setup_start_checks(self) -> None:
		self._own_checks = {check.cause: getattr(self, "_check_" + check.cause) for check in self.START_CHECKS if not check.source}
		self._substitution_gaps: Dict[Optional[str], Any] = {}      # acting seat -> the group that last had no option

	# ---- the test ---------------------------------------------------------------------------------------------

	def run_check(self, check: StartCheck, node_id: str, node: Dict[str, Any], ignore_trade: bool, memo: Any, why: bool) -> Verdict:
		if check.source:
			return getattr(self.needs, check.source)(node_id, node, ignore_trade, memo, why)
		return self._own_checks[check.cause](node_id, node, ignore_trade, memo, why)

	def start_check(self, node_id: str, ignore_trade: bool = False, memo: Any = None, why: bool = True) -> Tuple[bool, Any]:
		"""(True, None) when the project may begin now, else (False, the reason). `ignore_trade` skips only the "does
		the trade exist" checks, so auto-train can ask whether THIS is the one thing standing between the seat and
		starting. `memo` is the visibility descent's shared cache; `why` false builds no sentence."""
		node = self.needs.tree[node_id]
		if node is None:
			return False, ("no such node" if why else None)
		run_check = self.run_check
		for check in self.START_CHECKS:
			verdict = run_check(check, node_id, node, ignore_trade, memo, why)
			if verdict is not None:
				return verdict
		verdict = self.needs.extra_start_checks(node_id, node, ignore_trade, memo, why)
		if verdict is not None:
			return verdict
		return True, None

	# ---- the checks -------------------------------------------------------------------------------------------

	def _check_win_condition(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# A THRESHOLD GOAL, NOT A PROJECT: measured, not built. It completes itself the moment the live measurement
		# crosses the target, so it is never offered as something to start whatever its (zero) cost fields say.
		if node.get("win_condition"):
			return False, (("this is not something you build; it happens on its own once %s"
			                % self.needs.win_condition_text(node)) if why else None)
		return None

	def _check_already_done(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		if node_id in self.needs.techniques_held():
			# A MOTHBALLED WORK IS NOT FRESH RESEARCH, and it is not "already done" either: you know how, and the plant
			# is gone. `restore` puts it back at a fraction of the cost, so this is checked BEFORE the flat case.
			if node_id in self.needs.closures():
				return False, (('you built this once and let it go; you already know how, so restoring it is cheaper '
				                'than starting over: {"cmd":"restore","id":"%s"} for about %s'
				                % (node_id, self.needs.money_text(self.needs.reopen_fee(node_id)))) if why else None)
			return False, ("already done" if why else None)
		return None

	def _check_already_active(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		if node_id in self.needs.legacy_projects().active:
			return False, ("already active" if why else None)
		return None

	def _check_needs_first(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# NOT DEAR HERE, IMPOSSIBLE HERE: the answer itself is needed whatever `why` is; only the sentence is skippable.
		needed, reason = self.needs.needs_first(node_id, False)
		if needed:
			return False, (("%s. Build %s first and this opens with it" % (reason, needed)) if why else None)
		return None

	def _check_needs_held_herd(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# THE SAME GATE, WHEN WHAT IS MISSING IS LIVING STOCK: knowing the technique is not the blocker, so it is
		# reported as a supply gap.
		needed, reason = self.needs.needs_first(node_id, True)
		if needed:
			return False, (("%s. Build %s first and this opens with it" % (reason, needed)) if why else None)
		return None

	def _check_unobtainable(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		if node["cat"] == "unobtainable":
			return False, ("retired category: unobtainable in this tree" if why else None)
		return None

	def _check_foreign_only(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		if self.needs.foreign_only(node_id):
			return False, (("that is an institution of a different society. %s has "
			                "no such thing, and it is not something you can build "
			                "here" % self.needs.society_name()) if why else None)
		return None

	def _check_missing_prereqs(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		done = self.needs.techniques_held()
		missing = research_gate.unmet_prerequisites(node, lambda prereq_id: prereq_id in done)
		if missing:
			# NAME ONLY WHAT YOU HAVE HEARD OF: the sentence is built by knowledge's `prerequisite_message`, the one fog
			# filter for it. The boolean needs only that there ARE missing prerequisites.
			return False, (self.needs.prerequisite_message(missing, memo) if why else None)
		return None

	def _check_unheld_stock(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		return start_rules.unheld_stock_verdict(self.needs.stock_status[node_id]["missing"], why)

	def _check_substitution(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		if not self._substitution_quality(node_id)[1]:
			if not why:
				return False, None
			group, options = self._substitution_gaps.get(self.clock.acting_seat) or (None, [])
			seen = [option_id for option_id in options
			        if self.needs.tree[option_id] is None or self.needs.visibility(option_id, memo)]
			return False, ("this needs %s and you have none of the things that "
			               "would serve%s"
			               % (group or "a material or a vessel it can be built around",
			                  (": any of " + ", ".join(seen) + " would do") if seen else
			                  ", and none of them is anything you have heard of yet"))
		return None

	def _check_credit_frozen(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# A CREDIT FREEZE HAS TO APPLY TO THE PLAYER TOO: creditors seize CONCERNS, so a player who opens none could
		# otherwise default over and over for nothing but reputation, which regenerates.
		frozen_until = self.needs.debt_status()["credit_frozen_until"] or 0
		if self.needs.year() < frozen_until:
			if self._cash_covers_start(node_id):
				return None
			return False, (start_rules.credit_frozen_text(frozen_until, self.needs.horizon_end_year()) if why else None)
		return None

	def _check_arrears(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# Arrears blocks NEW commitments, with two escape hatches: creditors care about PERSISTENT insolvency, and
		# anything payable out of what is LEFT of this year's income needs nobody's permission. Revenue is worked out
		# only when the household has been insolvent long enough for it to matter.
		insolvent_years = self.needs.debt_status()["insolvent_years"]
		if insolvent_years < constants.ARREARS_GRACE_YEARS:
			return None
		needs = self.needs

		def surplus():
			return needs.revenue_estimate() - needs.upkeep() - needs.living_cost() - needs.mine_operating_cost()
		capital = needs.acting_balance()
		if start_rules.arrears_blocks(
				insolvent_years, constants.ARREARS_GRACE_YEARS, capital, surplus, lambda: needs.project_cost(node_id),
				needs.revenue_estimate, lambda: constants.ARREARS_CHEAP_PROJECT_FLOOR_LABOUR_HOURS * needs.money_per_labour_hour(),
				constants.ARREARS_CHEAP_PROJECT_SURPLUS_MULTIPLE,
				lambda: constants.ARREARS_HARD_STOP_FLOOR_LABOUR_HOURS * needs.money_per_labour_hour(),
				constants.ARREARS_HARD_STOP_REVENUE_MULTIPLE):
			return False, (("you have been in arrears %d years and are %s down; "
			                "nobody will fund a new undertaking of this size. Something "
			                "you can pay for out of this year's income is still allowed, "
			                "so is finishing or stopping what is running."
			                % (insolvent_years, needs.money_text(-capital))) if why else None)
		return None

	def _check_people_exist(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# Staffing demand against the people who exist, before any per-person hiring advice: no price or school makes
		# up a missing population.
		if ignore_trade:
			return None
		shortfall = self.needs.project_staffing_shortfall(node)
		if shortfall:
			return False, (shortfall if why else None)
		return None

	def _check_scholar_staff(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# SCHOLARS UNDER CONTRACT COUNT TOO (Complaints/34): hours already bought and paid for satisfy the requirement.
		hands = self.needs.hours_available["scholar_hands"]
		if research_gate.hands_short(node["sch"], hands) > 0.0:
			return False, (scholar_gate_text(node["sch"], hands, lambda deficit: self.needs.staff_advice("scholars", deficit))
			               if why else None)
		return None

	def _check_craft_staff(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# CRAFTSMEN YOU HAVE UNDER CONTRACT COUNT TOO: a year of a jobbing carpenter's time IS a carpenter, so the
		# figure can be fractional even when every person on the payroll is a whole one.
		hands = self.needs.hours_available["craft_hands"]
		if research_gate.hands_short(node["art"], hands) > 0.0:
			return False, (craftsmen_gate_text(node["art"], hands, lambda deficit: self.needs.staff_advice("artisans", deficit))
			               if why else None)
		return None

	def _check_absent_trades(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# THE TRADE HAS TO EXIST: a node wanting hours of an engineer cannot be built by smiths. You make one by
		# teaching one.
		absent = [] if ignore_trade else sorted(trade_id for trade_id in node["lab"] if not self.needs.trade_available[trade_id])
		if absent:
			if not why:
				return False, None
			return False, ("this needs %s and there are none in this society. Teach one: %s"
			               % (", ".join(trade_id + "s" for trade_id in absent),
			                  training_advice_text(self.needs.training_advice(absent[0]))))
		return None

	def _check_none_left_trades(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# AND SOMEBODY HAS TO BE LEFT: a trade you taught still counts as existing after the last of them has died or
		# been poached. People being TAUGHT count when they qualify before the stall gate would abandon the project.
		none_left = [] if ignore_trade else sorted(
			trade_id for trade_id, want in (node["lab"] or {}).items()
			if want > 0 and self.needs.market_supply[trade_id] <= 0.0 and self.trade_wait_outlasts(trade_id))
		if none_left:
			return False, (("this needs %s and there is not one left here to do "
			                "it: nobody holds the trade and nobody is being taught it "
			                "in time. Teach more: %s, or hire from your own if you have any"
			                % (", ".join(trade_id + "s" for trade_id in none_left),
			                   training_advice_text(self.needs.training_advice(none_left[0])))) if why else None)
		return None

	def _check_social_approval(self, node_id, node, ignore_trade, memo, why) -> Verdict:
		# SOCIAL APPROVAL GATE: some things the State does not want built, and no amount of money substitutes for
		# someone powerful being willing to be associated with it. The patronage and institution nodes are how you BUY
		# permission, so they cannot themselves require permission.
		if node["cat"] in SOCIAL_CATEGORIES:
			return True, None
		score = self.needs.state_interest(node)
		wary_patron = self.needs.approval_patron("wary")
		opposed_patron = self.needs.approval_patron("opposed")
		protection = self.needs.standing()["protection"]
		stance = start_rules.approval_stance(
			score, wary_patron, opposed_patron, lambda patron_id: self.needs.running[patron_id], protection,
			constants.STATE_WARY_THRESHOLD, constants.STATE_OPPOSED_THRESHOLD, constants.STATE_OPPOSITION_PROTECTION_OVERRIDE)
		if stance == "wary":
			# NAME THE NODE, by the word you would type, but only if the player has heard of it.
			return False, (("the state is wary of this (state interest %.1f); %s"
			                % (score, self._patron_advice(wary_patron, "a local patron's name behind you"))) if why else None)
		if stance == "opposed":
			return False, (("the state actively opposes this (state interest "
			                "%.1f); %s, or protection above %.2f (you have "
			                "%.2f)"
			                % (score, self._patron_advice(opposed_patron, "patronage at the very top"),
			                   constants.STATE_OPPOSITION_PROTECTION_OVERRIDE, protection)) if why else None)
		return None

	# ---- helpers the checks and the blocker list share ----------------------------------------------------------

	def _patron_advice(self, node_id: str, in_world: str) -> str:
		"""What to tell a player who needs `node_id` before they may begin: the id and the command only when they
		have heard of it, the same advice in plain words when they have not. The prerequisites are read directly,
		not through the test, which called this."""
		if not self.needs.visibility(node_id, None):
			return "you will need %s before anyone here will let you begin" % in_world
		done = self.needs.techniques_held()
		if node_id in done:
			return ("get %s: you have built it already, so 'open %s' to put "
			        "it behind you" % (in_world, node_id))
		missing = [prereq_id for prereq_id in self.needs.tree[node_id]["pre"] if prereq_id not in done]
		if missing:
			seen = [prereq_id for prereq_id in missing if self.needs.visibility(prereq_id, None)]
			return ("get %s first, which itself wants %s"
			        % (in_world, ", ".join(seen) if seen else "something you have not heard of yet"))
		return "get %s first: 'start %s'" % (in_world, node_id)

	def _owed_on_work_in_hand(self) -> float:
		active = self.needs.legacy_projects().active
		return sum(active[active_id].get("cost_left") or 0.0 for active_id in sorted(active))

	def _cash_covers_start(self, node_id: str) -> bool:
		"""True when cash in hand pays for this start on top of what work in hand still owes."""
		return funding.cash_covers_start(self.needs.project_cost(node_id), self.seat.paid_towards.get(node_id, 0.0),
		                                 self._owed_on_work_in_hand(), self.needs.acting_balance())

	def money_refusal(self, node_id: str, extra_owed: float = 0.0):
		"""Why the bill is past cash plus credit (materials due now included), or None. `extra_owed` is money
		already committed by starts not yet applied, counted like work in hand."""
		needs = self.needs
		price = needs.project_cost(node_id)
		refusal = needs.material_upfront_refusal(node_id)
		if refusal:
			return refusal
		# money already sunk into this node comes off the bill
		price -= funding.paid_credit(price, self.seat.paid_towards.get(node_id, 0.0))
		owed, ceiling, shortfall = start_money.start_shortfall(
			price, self._owed_on_work_in_hand(), extra_owed, needs.acting_balance(), needs.credit_limit())
		if shortfall > 0.0:
			money = needs.money_text
			return Refusal("cash_short",
			               "you already owe %s on work in hand; this "
			               "would take it to %s, and between cash and your credit line "
			               "you can raise %s, so you are %s short. Finish or stop "
			               "something first, or earn or pay down that amount.%s"
			               % (money(owed, True), money(owed + price, True), money(ceiling, True),
			                  money(owed + price - ceiling, True), needs.purchase_remedies_text()),
			               owed=owed, price=price, ceiling=ceiling, short=owed + price - ceiling)
		return None

	def _substitution_quality(self, node_id: str) -> Tuple[float, bool]:
		"""Resolve `req_any` groups: for each, the best option actually held. A steam engine does not REQUIRE coal and
		steel; it requires a fuel and a pressure vessel. Wood in a bronze boiler works, badly: the quality factor says
		how badly. The group that had no option is kept for the blocker list to name."""
		groups = self.needs.tree[node_id].get("req_any") or []
		if not groups:
			return 1.0, True
		done = self.needs.techniques_held()
		quality, ok, failed = start_rules.substitution_outcome(groups, lambda group: self._group_best(node_id, group, done))
		self._substitution_gaps[self.clock.acting_seat] = None if ok else start_rules.substitution_gap(failed)
		return quality, ok

	def _group_best(self, node_id: str, group: Dict[str, Any], done: Any) -> float:
		"""The best quality any option in one `req_any` group offers (the gate every actor passes)."""
		return research_gate.substitute_quality(
			self.needs.tree[node_id], group, lambda option: option in done,
			lambda option: self.needs.tree[option] is not None, constants.PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT)

	def last_substitution_gap(self) -> Any:
		return self._substitution_gaps.get(self.clock.acting_seat)

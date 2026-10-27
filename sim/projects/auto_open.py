"""Opening what plainly pays for itself, year by year: ordinary concerns best margin first, and the institutions a
household's capability depends on even at a loss it can carry.

Default ON for the optimizer and OFF for a player, like every other automation in this game."""
from sim.finance.api import deep_in_arrears, opens_in_deep_arrears, payback_years
from sim.reporting.api import RecordEvent
from sim.ventures.api import OpenVenture

from .constants import (AUTO_EXPAND_MIN_OCCUPANCY, AUTO_EXPAND_MIN_ROOM_UNITS, AUTO_EXPAND_MIN_STEP_UNITS,
                        AUTO_EXPAND_SURPLUS_SHARE, AUTO_OPEN_CREDIT_LINE_BLEED_SHARE, AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE,
                        AUTO_OPEN_INSTITUTION_ARREARS_SHARE, AUTO_OPEN_PAYBACK_LIMIT_YEARS, AUTO_OPEN_SURPLUS_SHARE_FOR_BLEED,
                        STARTER_FOUNDING_MIN_UNITS)


class AutoOpen:
	def auto_open_ventures(self):
		"""Open what plainly pays for itself, best margin first, within the staff and the money available. Default ON for
		the optimizer and OFF for a player, like every other automation in this game."""
		opened = []
		cands = self._auto_open_ordinary_candidates()
		# AUTO-OPENING ASKS "open", NOT "buy": a door on a concern that is already built and already earning pays for its
		# own fee, while a wage buys nothing back. Each of the three helpers below computes its own budget (_surplus,
		# _bleed_room, _line) or opens through the ventures' own `open`, which runs the real spending_power("open") gate on
		# its own account.
		_deep_arrears = self._auto_open_check_deep_arrears()
		caps = self._auto_open_institution_candidates(_deep_arrears)
		_surplus, _bleed_room = self._auto_open_institution_budget()
		newly_opened, _surplus, _bleed_room = self._auto_open_institutions(caps, _surplus, _bleed_room)
		opened.extend(newly_opened)
		newly_opened, _surplus = self._auto_expand_institutions(_surplus, _deep_arrears)
		opened.extend(newly_opened)
		newly_opened, blocked = self._auto_open_ordinary_ventures(cands, _deep_arrears)
		opened.extend(newly_opened)
		self._auto_open_log_blocked(blocked, opened)
		return opened

	def _open_venture(self, node_id, units=None):
		"""(did it open, the reply): the ventures' `open`, asked through its command."""
		return self.needs.send(OpenVenture(node_id, units))

	def _auto_open_ordinary_candidates(self):
		"""Ordinary, completed, net-positive concerns not yet running, best margin for the money they tie up first.

		BEST MARGIN FOR THE MONEY IT TIES UP, not best margin outright. When what you can raise is the binding
		constraint - which is exactly when this matters - a 400-a-year shop that opens for 60 is worth more than a
		3,200-a-year works you cannot afford at all. sorted() is stable, so ties keep the order of the input - and the
		input was a generator over a set, so `done` is sorted first."""
		needs = self.needs
		nodes = needs.tree_nodes()
		operating = needs.operating()
		return sorted((node_id for node_id in sorted(needs.legacy_projects().done)
		               if needs.is_venture[node_id] and node_id not in operating
		               and not self.exclusion_reason(node_id)
		               and nodes[node_id]["rev"] > nodes[node_id]["up"]),
		              key=lambda k: -((nodes[k]["rev"] - nodes[k]["up"]) / max(1.0, needs.venture_capex[k])))

	def _auto_open_check_deep_arrears(self):
		"""Whether the household is deep enough in arrears that a NEW institution's standing bleed is gated.

		DEEP IN ARREARS IS NOT "IN ARREARS": a household in the red must still be able to open the shop that would dig it
		out, so the gate cannot be `capital <= 0`. But with no gate at all, opening a new institution - a standing bleed
		against money not yet coming in - becomes unconstrained borrowing. Half the credit line is the line: below it you
		can still open your way out, above it you are digging.

		A completed, ordinary, net-positive concern is a different thing, and gating it on household-wide arrears is the
		wrong test: its own payback period, not the size of the hole the household is in, is what should decide it (see
		_auto_open_ordinary_ventures). "open", NOT "buy": opening an already-built, already-earning concern must IGNORE
		how deep the household already is, since refusing it only leaves its capex sunk and earning nothing for as long
		as the arrears last. spending_power() must not be reused here: it answers a different question."""
		needs = self.needs
		return deep_in_arrears(needs.acting_balance(), needs.credit_limit(None, None, None), AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE)

	def _auto_open_institution_candidates(self, _deep_arrears):
		"""Capability institutions not yet running, that a founder could open at a loss the household can carry.

		AND THE ONES WHOSE WORTH IS NOT AT THE DOOR. A school takes 2,500 a year and hands back 800, so the margin test
		shuts it out for ever - and a school is where twelve of your scholars come from. Everything a capability is gated
		on has to be able to open on the strength of the capability, at a loss, provided the loss is one the household
		can actually carry. Cheapest to keep first, so a poor founder gets the workshop and the local patron before the
		academy. STILL NOTHING WHILE DEEP IN ARREARS: an institution is a standing bleed against revenue the household
		does not have, exactly the unconstrained-borrowing case the comment above warns about."""
		needs = self.needs
		nodes = needs.tree_nodes()
		capability = needs.capability_sets()[0]
		operating = needs.operating()
		return [] if _deep_arrears else sorted(
			(node_id for node_id in sorted(needs.legacy_projects().done)
			 if node_id in capability
			 and node_id not in operating and needs.is_venture[node_id]
			 and not self.exclusion_reason(node_id)
			 and nodes[node_id]["rev"] <= nodes[node_id]["up"]),
			key=lambda k: (nodes[k]["up"] - nodes[k]["rev"], needs.venture_capex[k], k))

	def _auto_open_institution_budget(self):
		"""How much real surplus, and how much standing bleed against it, a new institution may be opened or grown with
		this year.

		WHAT IS LEFT AFTER EVERYTHING YOU ARE ALREADY COMMITTED TO. AN INSTITUTION IS AN INVESTMENT, AND A LENDER KNOWS
		IT: requiring a CURRENT surplus creates a catch-22, where an institution that would itself supply the household's
		places, staff and workshop capacity can never open, because surplus stays negative precisely for lack of the
		institution. So an institution may be opened against what you could RAISE and not only out of what you are
		clearing - with two guards: nothing opens while you are deep in arrears, and the standing bleed you take on may
		not outgrow a tenth of your line."""
		needs = self.needs
		capital = needs.acting_balance()
		_surplus = (needs.revenue_estimate() - needs.upkeep() - needs.living_cost(None, None, None))
		_line = needs.credit_limit(None, None, None)
		_deep = capital < 0 and -capital > _line * AUTO_OPEN_INSTITUTION_ARREARS_SHARE
		_bleed_room = (max(0.0, _surplus) * AUTO_OPEN_SURPLUS_SHARE_FOR_BLEED
		               + (0.0 if _deep else _line * AUTO_OPEN_CREDIT_LINE_BLEED_SHARE))
		return _surplus, _bleed_room

	def _auto_open_institutions(self, caps, _surplus, _bleed_room):
		"""Open institution candidates that fit inside this year's bleed room, at full size if it fits or as a smaller
		starter founding if it does not."""
		needs = self.needs
		nodes = needs.tree_nodes()
		scalable = needs.capability_sets()[1]
		opened = []
		for node_id in caps:
			_bleed = needs.institution_upkeep(node_id, None, False) - nodes[node_id]["rev"]
			if _bleed <= _bleed_room:
				did_open, _message = self._open_venture(node_id)
				if did_open:
					opened.append(node_id)
					_surplus -= _bleed
					_bleed_room -= _bleed
				continue
			# TOO DEAR AT FULL SIZE - FOUND IT SMALLER. workshop_first bled 900 a year against a surplus that was negative
			# BECAUSE there was no workshop, so the full-size gate above refused it for four and a half centuries
			# straight. A place you can only afford a fifth of is still a place; institution_units below 1.0 is what
			# `open` calls a starter founding.
			if node_id not in scalable or _bleed <= 0:
				continue
			starter = max(0.0, min(1.0, _bleed_room / _bleed))
			if starter < STARTER_FOUNDING_MIN_UNITS:
				continue
			did_open, _message = self._open_venture(node_id, starter)
			if did_open:
				opened.append(node_id)
				_spent = _bleed * starter
				_surplus -= _spent
				_bleed_room -= _spent
		return opened, _surplus, _bleed_room

	def _auto_expand_institutions(self, _surplus, _deep_arrears):
		# CLIMB THE LADDER ONCE IT IS OPEN - BUT ONLY ON REAL MONEY AND REAL DEMAND, NOT ON THE STARTER FOUNDING'S CREDIT
		# ALLOWANCE: `_bleed_room` includes a tenth of the credit line, the borrowing allowance the starter founding
		# genuinely needs to break the initial deadlock. Reusing it here to grow an already-open institution would look
		# affordable most years without ever checking whether the household could actually CARRY the resulting upkeep
		# against its actual revenue. So: real cash flow only (no credit line here), and only when the place is actually
		# full enough to want more room.
		needs = self.needs
		nodes = needs.tree_nodes()
		opened = []
		operating = needs.operating()
		if _surplus > 0.01 and not _deep_arrears:
			for node_id in sorted(needs.capability_sets()[1]):
				if node_id not in operating or _surplus <= 0.01:
					continue
				have = needs.institution_units[node_id]
				ceiling = needs.institution_unit_ceiling[node_id]
				room = ceiling - have
				if room < AUTO_EXPAND_MIN_ROOM_UNITS:
					continue
				places_now = needs.institution_places[node_id] * have
				if needs.headcount() < places_now * AUTO_EXPAND_MIN_OCCUPANCY:
					continue        # not full enough yet to be worth more
				per_unit = nodes[node_id]["up"] - nodes[node_id]["rev"]
				# AT MOST A QUARTER OF THIS YEAR'S REAL SURPLUS, and at most one further unit a year - growth, not a
				# second bootstrap.
				afford_room = _surplus * AUTO_EXPAND_SURPLUS_SHARE
				step = min(1.0, room) if per_unit <= 0 else max(0.0, min(1.0, room, afford_room / per_unit))
				if step < AUTO_EXPAND_MIN_STEP_UNITS:
					continue
				did_open, _message = self._open_venture(node_id, step)
				if did_open:
					opened.append(node_id)
					_spent = max(0.0, per_unit) * step
					_surplus -= _spent
		return opened, _surplus

	def _auto_open_ordinary_ventures(self, cands, _deep_arrears):
		# A CONCERN THAT PAYS FOR ITS OWN DOOR WITHIN A SEASON OR TWO IS A DIFFERENT CASE FROM UNCONSTRAINED BORROWING:
		# that failure mode is ventures whose capex is large against their annual net - borrow to the hilt, and the debt
		# outruns what they pay back before they even finish ramping up. A venture whose capex clears inside
		# PAYBACK_LIMIT_YEARS is the opposite case: refusing it while deep in arrears leaves its capex sunk for nothing,
		# which helps neither the household nor whoever it owes. `open` still refuses, on its own numbers, anything whose
		# capex cannot actually be raised or whose supervision cannot actually be staffed - this only widens what is even
		# offered to it while the household is deep in arrears.
		needs = self.needs
		nodes = needs.tree_nodes()
		opened = []
		PAYBACK_LIMIT_YEARS = AUTO_OPEN_PAYBACK_LIMIT_YEARS
		blocked = None
		for node_id in cands:
			# NO SECOND, STRICTER GATE. This broke out the moment capital went negative, so a household in arrears could
			# never open anything - and opening a concern is the only way to stop being in arrears. `open` already
			# refuses what you cannot raise, and a lender will advance against a shop with stock in it as readily as
			# against half-built work.
			if _deep_arrears:
				node = nodes[node_id]
				_payback = payback_years(needs.venture_capex[node_id], node["rev"], node["up"])
				if not opens_in_deep_arrears(_payback, PAYBACK_LIMIT_YEARS):
					if blocked is None:
						blocked = (node_id, ("it would take %.1f years to pay for its "
						                     "own doors, and nothing slower than %.0f "
						                     "opens while you are this deep in arrears; "
						                     "clear enough debt to cross half your "
						                     "credit line, or wait for it to look "
						                     "quicker against what you can raise"
						                     % (_payback, PAYBACK_LIMIT_YEARS)))
					continue
			did_open, why = self._open_venture(node_id)
			if did_open:
				opened.append(node_id)
			elif blocked is None:
				blocked = (node_id, why)
		return opened, blocked

	def _auto_open_log_blocked(self, blocked, opened):
		"""Say why the best candidate stayed shut, if nothing at all opened this year: a policy that silently declines is
		indistinguishable from a policy that is broken. Throwing away every refusal `open` hands back would let a concern
		earning far more than its upkeep sit closed indefinitely with the policy switched on."""
		if blocked and not opened:
			needs = self.needs
			node_id, why = blocked
			scenario_year = needs.year()
			said = self.seat.said_autoopen or {}
			if scenario_year - said.get(node_id, -99) >= 10:
				said[node_id] = scenario_year
				self.seat.said_autoopen = said
				node = needs.tree_nodes()[node_id]
				needs.send(RecordEvent.in_year(scenario_year, "concern_unprofitable", "%s would earn %s a year against %s of upkeep and "
				           "is still shut: %s"
				           % (node_id, needs.money_text(node["rev"], grouped=True),
				              needs.money_text(node["up"], grouped=True),
				              why or "something is in the way")))

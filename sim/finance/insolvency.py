"""What happens as the acting seat crosses its credit limit: the founder's responses to exhausted credit, then entry into service or
a settlement that writes most of the debt off; the insolvency count, and the year of service a bonded debtor works off.

Needs: acting_balance, legacy_acting_household, legacy_household_actor, legacy_edge_account, legacy_projects, legacy_game (the
ventures' review and the people freed, until production and workforce move), standing, money_text, civilisation, revenue_estimate,
upkeep, mine_operating_cost, game_config, labour_market, money_per_labour_hour."""
from typing import Any

from sim.agents.api import business_review, edges, ledger
from sim.polity.api import SetReputation
from sim.reporting.api import RecordEvent
from sim.resources.api import MothballMines
from sim.workforce.api import BleedStaff, DisperseDependants

from . import rules
from .affordability import reputation_hit_taken
from .constants import (BONDAGE_LABOUR_SHARE, BONDAGE_WAGE_MARKUP, CREDIT_FREEZE_YEARS_AFTER_HALT, DEBT_BONDAGE_DEFAULT_TERM_YEARS,
                        HOUSEHOLD_DISPERSAL_ARTISANS_FLOOR, HOUSEHOLD_DISPERSAL_ARTISANS_RETENTION, INSOLVENCY_ARTISAN_FLOOR,
                        INSOLVENCY_BLEED_CAP, INSOLVENCY_BLEED_RATE, INSOLVENCY_FLOOR_MIN_LABOUR_HOURS,
                        INSOLVENCY_FLOOR_REVENUE_MULTIPLE, INSOLVENCY_SCHOLAR_BLEED_DISCOUNT, INSOLVENCY_SCHOLAR_FLOOR,
                        INSOLVENCY_YEARS_BEFORE_BLEED, SETTLEMENT_CAPITAL_RETAINED_FRACTION, SETTLEMENT_CREDIT_FREEZE_YEARS,
                        SETTLEMENT_REPUTATION_HIT)
from .credit_freeze import halt_active_projects, settlement_freeze, settlement_owed


class Insolvency:

	def enforce_credit_limit(self, year: int) -> None:
		"""Nobody lends past the limit, so past the limit you simply stop: the founder's own responses to exhausted credit, which
		come before any default. Default itself is the shared arrears rule (`charge_interest`, then `default_on_debt`)."""
		self.answer_exhausted_credit(year)

	def default_on_debt(self, year: int) -> None:
		"""The lenders default the founder's debt after too many years of arrears: first the responses to exhausted credit, then
		entry into service for a civilisation that had it, otherwise a settlement that writes most of the debt off. The household
		is left poor rather than impossibly indebted, which is a position it can work out of."""
		self.answer_exhausted_credit(year)
		limit = self.credit_limit()
		if self.needs.acting_balance() >= -limit:
			return
		if self.enter_debt_bondage(year):
			return
		self.settle_insolvency(year, limit)

	def answer_exhausted_credit(self, year: int) -> None:
		"""Past the limit, in this order: stop paying for new work, let go of what cannot be maintained, and shed the household
		that can no longer be fed."""
		needs = self.needs
		limit = self.credit_limit()
		household = needs.legacy_acting_household()
		projects = needs.legacy_projects()
		if household.capital >= -limit:
			return
		# stop everything in progress: it cannot be funded
		if projects.active:
			dropped, kept = halt_active_projects(projects)
			household_seat = self.seat
			household_seat.credit_frozen_until = year + CREDIT_FREEZE_YEARS_AFTER_HALT
			needs.send(RecordEvent.of("credit_exhausted", "CREDIT EXHAUSTED: %d project%s stopped, "
				"unfinished: %s. The %s already paid "
				"stands to your credit and comes off the "
				"bill if you begin again. Nobody will fund new "
				"work here until %d"
				% (len(dropped), "" if len(dropped) == 1 else "s",
				   ", ".join(dropped[:4]) + (" and others" if len(dropped) > 4 else ""),
				   needs.money_text(kept, grouped=True), year + CREDIT_FREEZE_YEARS_AFTER_HALT),
				stopped=list(dropped), frozen_until=year + CREDIT_FREEZE_YEARS_AFTER_HALT))
		# let go of what cannot be maintained
		if household.capital < -limit:
			needs.send(MothballMines())
		if household.capital < -limit:
			# a creditor takes the business (the plants it runs), never the knowledge of how they work
			taken = [closure.entry_key for closure in needs.legacy_game().review_ventures((business_review.CREDITOR_SEIZURE,), year)]
			# only say it if it happened, and name them
			if taken:
				needs.send(RecordEvent.of("creditors_took", "creditors took what they could: %d concerns "
					"closed and sold up: %s. You keep the "
					"knowledge; reopening means paying for the "
					"premises again" % (len(taken), ", ".join(taken))))
		# and the household goes: nobody keeps four hundred dependants they cannot feed. People are sold or freed and they
		# leave, and shedding them is how the household becomes solvent again.
		staff = needs.staff()
		if household.capital < -limit and (staff["slaves"] or staff["freedmen"]):
			freed = staff["slaves"] + staff["freedmen"]
			needs.legacy_game().labour.manumit(staff["slaves"])          # they are not sold on
			needs.send(DisperseDependants(HOUSEHOLD_DISPERSAL_ARTISANS_FLOOR, HOUSEHOLD_DISPERSAL_ARTISANS_RETENTION))
			needs.send(RecordEvent.of("household_disperses", "the household disperses: %d people leave, because "
				"you can no longer feed them" % freed))

	def debt_bondage_term_years(self) -> float:
		"""Years of service a default costs in this society; zero where it had no debt bondage. The founder's default and every
		household cohort's in the economy follow this one rule."""
		civilisation = self.needs.civilisation()
		if not civilisation.get("debt_bondage"):
			return 0.0
		return float(civilisation.get("bondage_years", DEBT_BONDAGE_DEFAULT_TERM_YEARS))

	def enter_debt_bondage(self, year: int) -> bool:
		"""Where the society had debt bondage, a default puts the debtor into service for a term worked off, as the Han debt
		servitude, the Norse debt-thrall and the Mexica tlacotin were; whether it did. Rome abolished it, so Rome goes straight to
		the write-off. In service the hours are not the debtor's own, and the term ends sooner if the work is worth something."""
		needs = self.needs
		seat = self.seat
		term = self.debt_bondage_term_years()
		if term > 0.0 and not seat.bondage_years_left:
			seat.bondage_years_left = term
			seat.bondage_debt = -needs.acting_balance()
			ledger.settle(needs.legacy_household_actor(), needs.legacy_edge_account[edges.EDGE_CREDITORS], 0.0, "debt taken into bondage")
			needs.send(RecordEvent.of("debt_bondage", "BONDAGE: you cannot pay, and you enter service for "
				"your debt. For about %d years most of your hours "
				"belong to someone else. It is not the end: it is "
				"worked off, and then you are free again" % term))
			return True
		return False

	def settle_insolvency(self, year: int, limit: float) -> None:
		"""The lenders write most of the debt off. The household keeps its standing, its knowledge and its practice, which is
		what it started with."""
		needs = self.needs
		seat = self.seat
		seat.last_settlement = year
		# the balance left is measured against the line that stands once the name has been marked down, so it never starts outside it
		reputation_before = needs.standing()["reputation"]
		needs.send(SetReputation(max(0.0, reputation_before - SETTLEMENT_REPUTATION_HIT)))
		owed = settlement_owed(limit, self.credit_limit(), SETTLEMENT_CAPITAL_RETAINED_FRACTION)
		needs.send(SetReputation(reputation_before))
		ledger.settle(needs.legacy_household_actor(), needs.legacy_edge_account[edges.EDGE_CREDITORS], -owed, "debts written off in settlement")
		# the number announced has to be the number applied
		reputation_hit = reputation_hit_taken(SETTLEMENT_REPUTATION_HIT, needs.standing()["reputation"])
		needs.send(SetReputation(max(0.0, needs.standing()["reputation"] - SETTLEMENT_REPUTATION_HIT)))
		# and nobody lends for a while: walking away from a debt must cost more than a little standing, which grows back
		frozen_before = seat.credit_frozen_until
		seat.credit_frozen_until, moved = settlement_freeze(frozen_before, year, SETTLEMENT_CREDIT_FREEZE_YEARS)
		needs.send(RecordEvent.of("insolvency_settled", "INSOLVENCY SETTLED: most of the debt is written "
			"off and you still owe about %s. Your "
			"name is worth less for it (reputation %s), and "
			"you keep your knowledge and your practice%s"
			% (needs.money_text(owed, grouped=True),
			   "-%.1f" % reputation_hit if reputation_hit > 0.05 else "already at nothing, so no further",
			   (". Settling again while still frozen out "
			    "pushes the date nobody will fund you "
			    "again until from %d out to %d - it moves "
			    "with every settlement, not just the first" % (frozen_before, seat.credit_frozen_until)) if moved else ""),
			reputation_hit=reputation_hit, credit_frozen_until=seat.credit_frozen_until, freeze_moved=bool(moved),
			frozen_before=frozen_before))

	def judge_insolvency(self, command: Any = None) -> None:
		"""Insolvency must have a consequence, the realistic one: nobody arrests you for debt, but the people you cannot pay stop
		turning up and nobody extends credit for new work while you are in arrears. Being in debt is not being insolvent: a
		household running a surplus is paying its creditors, and the year counts only for one whose income does not cover its
		costs. The staff who leave are bounded by a floor, so insolvency costs the expansion without trapping the household."""
		needs = self.needs
		seat = self.seat
		household = needs.legacy_acting_household()
		if household.capital < 0:
			net = (needs.revenue_estimate() - needs.upkeep() - self.recurring_living_cost(needs.revenue_estimate(), needs.upkeep())
			       - needs.mine_operating_cost())
			if net > 0:
				seat.insolvent_years = 0
			else:
				seat.insolvent_years = seat.insolvent_years + 1
			floor = -max(self.priced(INSOLVENCY_FLOOR_MIN_LABOUR_HOURS), needs.revenue_estimate() * INSOLVENCY_FLOOR_REVENUE_MULTIPLE)
			if household.capital < floor and seat.insolvent_years >= INSOLVENCY_YEARS_BEFORE_BLEED:
				bleed = min(INSOLVENCY_BLEED_CAP, INSOLVENCY_BLEED_RATE * seat.insolvent_years)
				needs.send(BleedStaff(bleed, INSOLVENCY_ARTISAN_FLOOR, INSOLVENCY_SCHOLAR_FLOOR, INSOLVENCY_SCHOLAR_BLEED_DISCOUNT))
				if seat.insolvent_years in (3, 6, 12, 25):
					needs.send(RecordEvent.of("arrears_staff_leaving", "IN ARREARS for %d years: staff are leaving "
						"because you cannot pay them" % seat.insolvent_years))
		else:
			seat.insolvent_years = 0

	def serve_bondage_year(self, command: Any = None) -> None:
		"""Serving out a debt: the hours owed go to the creditor and the debt falls; when it is done the household is free, and
		keeps everything it knows."""
		needs = self.needs
		seat = self.seat
		if seat.bondage_years_left > 0:
			repayment = rules.bondage_repayment(needs.game_config()["founder_hours_per_year"], BONDAGE_LABOUR_SHARE,
			                                    BONDAGE_WAGE_MARKUP, needs.labour_market().quote("labourer"))
			seat.bondage_years_left, seat.bondage_debt, served = rules.serve_bondage_year(
				seat.bondage_years_left, seat.bondage_debt, repayment)
			if served:
				needs.send(RecordEvent.of("bondage_served", "your term is served and the debt is discharged; "
					"you are your own man again"))

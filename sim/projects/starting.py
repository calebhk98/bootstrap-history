"""Beginning, stopping and buying a project, and buying off scandal: the commands the projects module applies.

`start_project` is the PLAYER-CHOSEN start. It applies the same legality test as the optimizer's loop and, if it
passes, takes the shared research path (sim/agents/research.py, every actor's start) with this seat as the researcher.
In `--manual` mode the optimizer's loop is switched off, so this is then the only way anything starts."""
from typing import Any, Dict, Optional, Tuple

from sim.agents.api import CommandRejected, edges, research
from sim.ledger.api import PayEdge

from . import bribe_rules, constants, funding, instantaneous, record_rules, start_rules
from .commands import Bribe, PostBounty, StartProject, StopProject
from .needed_commands import (ChangeStanding, ClearMothball, CompleteProject, NoteSpend, RecordEvent,
                              SettleProjectMaterials)
from .researcher import SeatResearcher

BOUNTY_CRAFT_CATEGORIES = ("glass_optics", "metallurgy", "precision", "power", "agriculture", "information", "instruments")


class Starting:
	def _setup_starting(self) -> None:
		self.last_materials_paid = 0.0           # money the last start spent on materials now (not saved)

	# ---- registering a project ----------------------------------------------------------------------------------

	def initialize_project(self, node_id: str, *, ph_left: Optional[float] = None, spent: float = 0.0,
	                       cost_left: Optional[float] = None, include_labour: bool = True,
	                       bill: Optional[float] = None) -> Dict[str, Any]:
		"""Create and register one consistently-shaped active project."""
		node = self.needs.tree[node_id]
		if node is None:
			raise ValueError("unknown project %s" % node_id)
		active = self.needs.legacy_projects().active
		if node_id in active:
			raise ValueError("project %s is already active" % node_id)
		own_output_claim = None
		if cost_left is None:
			own_output_claim = self.needs.own_output_claim(node_id)
			bill, _materials_paid_now = self.needs.send(SettleProjectMaterials(node_id))
			cost_left = bill
		record = record_rules.new_record(node, self.needs.rebuild_work_factor(node_id), ph_left, spent, cost_left,
		                                 include_labour, bill, own_output_claim)
		active[node_id] = record
		return record

	def begin_project(self, node_id: str, precaution: bool = False) -> str:
		"""Put the seat's project in hand once the shared gates have passed: buy the materials due now, take the
		bill, register the project (what `research.begin` asks of the seat). Answers "begun", or "done" for a
		capability that needs no year."""
		needs = self.needs
		projects = needs.legacy_projects()
		node = needs.tree[node_id]
		# Materials due now are bought (and banked as stock) first; what is left is the bill paid in instalments.
		bill, materials_paid_now = needs.send(SettleProjectMaterials(node_id))
		if precaution:
			bill += needs.precaution_extra_cost(node_id, bill)
		price = bill
		paid_now = funding.paid_credit(price, (projects.paid_towards or {}).get(node_id, 0.0))
		price -= paid_now
		# CREDIT FOR WHAT YOU ALREADY PAID: when the creditors stop a project the money already sunk into it is kept
		# against the node, and this is where it comes back off the bill.
		if projects.paid_towards:
			projects.paid_towards.pop(node_id, None)          # spent once; the figure is `paid_now` above
		# A THING YOU ARE REBUILDING IS NOT A THING SITTING IDLE: a stale mothball entry would hide the node from
		# `available` and make `restore` claim it can reopen it.
		needs.send(ClearMothball(node_id))
		# lab_left STARTS FULL, SET HERE, not lazily the first time the year's labour is drawn: a lazy start reads a
		# project already most of the way through its founder-hours and wrongly concludes the hired-labour total is
		# nearly done too.
		self.initialize_project(node_id, spent=paid_now, cost_left=price, bill=bill)
		self.last_materials_paid = materials_paid_now
		if precaution:
			record = projects.active[node_id]
			record["precaution"] = True
			record["ph_left"] += needs.precaution_extra_hours(node_id)
		# A genuinely instantaneous capability should not need an otherwise empty annual turn merely to trip the
		# completion check. Anything with money, labour, risk, or a calendar floor stays on the normal path.
		if instantaneous.is_instantaneous(node["ph"], needs.calendar_floor(node_id), price, node["lab"], needs.effective_risk(node_id)):
			needs.send(CompleteProject(node_id))
			return "done"
		if paid_now > 0.5:
			needs.send(RecordEvent("project_restarted", "%s begun again; the %s already "
			                       "paid on it before comes off the bill"
			                       % (node_id, needs.money_text(paid_now, True))))
		# A thing you just chose to work on should get first call on your own hours.
		order = needs.legacy_order()
		if node_id in order:
			order.remove(node_id)
		order.insert(0, node_id)
		return "begun"

	# ---- the commands -------------------------------------------------------------------------------------------

	def start_project(self, command: StartProject) -> Tuple[bool, Any]:
		refusal = self.needs.start_refusal(command.node_id)       # the quote the player was shown, adjusters included
		if refusal:
			return False, refusal
		if command.precaution and self.needs.precaution_spec(command.node_id) is None:
			return False, "%s offers no pilot plant or redundant team to pay for." % self.needs.tree[command.node_id]["name"]
		try:
			research.begin(SeatResearcher(self, command.precaution), command.node_id, self.needs.research_world())
		except CommandRejected as reason:
			return False, reason.args[0]
		return True, None

	def stop_project(self, command: StopProject) -> Tuple[bool, str]:
		"""Stop a project you started. Your HOURS are gone; the money stands.

		Money already spent stands against the node, the same credit the credit limit keeps, and comes off the bill if
		you begin again: burning both would make stopping something yourself cost exactly as much as letting the
		creditors take it, so no branch would ever make `stop` the right move."""
		projects = self.needs.legacy_projects()
		if command.node_id not in projects.active:
			return False, "not active"
		project_state = projects.active.pop(command.node_id)
		projects.bountied.discard(command.node_id)
		if projects.paid_towards is None:
			projects.paid_towards = {}
		kept, credit = record_rules.credit_kept(project_state.get("spent", 0.0), projects.paid_towards.get(command.node_id, 0.0))
		if credit is not None:
			projects.paid_towards[command.node_id] = credit
		money = self.needs.money_text(kept, True)
		return True, ("stopped. The %s already paid stands to your "
		              "credit and comes off the bill if you begin again; the "
		              "hours are gone" % money if kept > 0.5 else "stopped; nothing had been paid yet")

	def bounty_eligible(self, node_id: str) -> bool:
		"""Can this be bought as a prize instead of built with your own hands?

		A public prize converts money into someone else's HOURS. It only works where the craft already exists in the
		society and the artisan can recognise success without understanding the theory: you cannot post a bounty for
		zone refining, nobody would know what to aim at. The category list is the default scenario's crafts; anything
		this society is measurably GOOD at (its own cost multipliers say so) is recognised too."""
		node = self.needs.tree[node_id]
		done = self.needs.techniques_held()
		return start_rules.bounty_possible(
			node["cat"], BOUNTY_CRAFT_CATEGORIES, all(prereq_id in done for prereq_id in node["pre"]),
			lambda: self.needs.civ_cost_factor(node_id), constants.BOUNTY_ELIGIBLE_COST_ADVANTAGE)

	def post_bounty(self, command: PostBounty) -> bool:
		"""Pay well over the odds so someone else does the work; gain visibility."""
		needs = self.needs
		node = needs.tree[command.node_id]
		price = needs.bounty_price(command.node_id)
		if price > needs.acting_balance():
			return False
		needs.send(PayEdge(edges.EDGE_WORKERS, price, "bounties posted"))
		needs.send(NoteSpend(price))
		needs.legacy_acting_household().bounties_paid += 1
		# The prize pays for all the work: no poster hours, no hired trades.
		self.initialize_project(command.node_id, ph_left=0.0, spent=price, cost_left=0.0, include_labour=False)
		projects = needs.legacy_projects()
		projects.active[command.node_id]["lab_left"] = {}
		projects.bountied.add(command.node_id)
		# A public prize makes you conspicuous: that is what `scandal` and `eminence` measure.
		needs.send(RecordEvent("bounty_posted", "posted a public bounty for %s (%s)"
		                       % (node["name"], needs.money_text(price, True, True))))
		return True

	def bribe(self, command: Bribe) -> Tuple[bool, str]:
		"""Pay your way out of trouble, deliberately, for a stated sum."""
		needs = self.needs
		amount = float(command.amount)
		standing = needs.standing()
		capital = needs.acting_balance()
		income = max(1.0, needs.revenue_estimate())
		weight = needs.value_weight["bribability"]
		per_point = constants.BRIBE_LABOUR_HOURS_PER_SCANDAL_POINT * needs.money_per_labour_hour()
		refusal = bribe_rules.refusal_for(amount, capital, standing["scandal"], standing["bribes_year_to_date"], income, weight,
		                                  constants.BRIBE_MEMORY_DECAY, constants.BRIBE_PROTECTION_CAP, constants.BRIBE_INCOME_SHARE)
		if refusal is not None:
			return False, self._bribe_refusal_text(refusal, amount, capital)
		plan = bribe_rules.plan(amount, standing["scandal"], standing["bribes_year_to_date"], income, weight,
		                        constants.BRIBE_MEMORY_DECAY, constants.BRIBE_PROTECTION_CAP, constants.BRIBE_INCOME_SHARE, per_point)
		needs.send(PayEdge(edges.EDGE_OFFICIALS, plan.paid, "bribes"))
		needs.send(ChangeStanding(plan.scandal, plan.bribes_year_to_date))
		return True, self._bribe_text(standing, needs.standing(), plan)

	def _bribe_refusal_text(self, refusal: bribe_rules.BribeRefusal, amount: float, capital: float) -> str:
		money = self.needs.money_text
		if refusal.cause == "not_positive":
			return "amount must be greater than zero. Nothing was changed."
		if refusal.cause == "over_capital":
			return "you have %s" % money(capital)
		if refusal.cause == "too_little":
			return ("you have no scandal to answer, and %s "
			        "is too little to buy any advocacy "
			        "worth having. About %s would begin to move "
			        "your protection. Nothing was changed." % (money(amount, True), money(refusal.floor, True)))
		return ("you have no scandal to answer and you are already "
		        "as protected as money can make you here, so this "
		        "would buy nothing. Nothing was changed.")

	def _bribe_text(self, before: Dict[str, float], after: Dict[str, float], plan: bribe_rules.BribePlan) -> str:
		"""BOTH THINGS IT BUYS: a bribe against zero scandal still feeds the year's bribes into protection, which keeps
		an accusation from being made in the first place. Reporting only the half that did not move would make a real
		effect look like money silently burned."""
		money = self.needs.money_text
		message = "scandal %.2f -> %.2f for %s" % (before["scandal"], after["scandal"], money(plan.paid))
		if plan.refused > 0.5:
			message += ("; %s of what you offered was not taken, because "
			            "this is as far as money goes here - you kept it" % money(plan.refused, True))
		if after["protection"] > before["protection"] + 0.0005:
			message += ("; advocacy and piety bought as well: protection %.2f -> %.2f"
			            % (before["protection"], after["protection"]))
		elif before["scandal"] <= bribe_rules.NO_SCANDAL:
			message += ("; you had no scandal to answer and are already as protected "
			            "as money can make you, so this bought nothing")
		return message

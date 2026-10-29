"""Shutting a completed work down on purpose to stop paying its upkeep, and bringing it back."""
from sim.agents.api import edges
from sim.knowledge.api import LearnTechnique
from sim.ledger.api import PayEdge
from sim.refusal import LogLine, Refusal

from sim.ventures.api import CloseConcern, RestoreConcern

from .closure_grace import grace_note, within_grace
from .constants import STAFF_CLOSURE_GRACE
from sim.reporting.api import NoteConcernChange


class Mothball:
	def mothball_work(self, node_id):
		"""Shut a completed work down to stop paying its upkeep.

		The lever for a finished, running institution that is a drag on upkeep, distinct from `stop` (which only cancels
		work still in progress) - without it, the only way to change what a household is paying for is to start MORE
		things. It is not free: you lose what the work gave you, and restoring it costs a fraction of building it."""
		needs = self.needs
		nodes = needs.tree_nodes()
		if node_id not in nodes:
			return False, "no such node"
		if node_id not in needs.techniques_held():
			return False, "you have not built that"
		if node_id in needs.techniques_granted():
			return False, ("that is something the society has, not something you "
			               "maintain; there is no upkeep of yours to stop")
		# MONEY IS NOT THE ONLY THING THIS TOOL CAN FREE: refusing whenever upkeep is zero, on the theory that nothing would
		# be saved, is true of the money and false of the staff - a concern with no money upkeep at all can still tie up a
		# fraction of a scholar or craftsman (a going concern's "your people already spoken for" table), which is exactly
		# the fraction a player can be short of even when there is "nothing to save" in money terms. Ask what THIS tool
		# actually releases (money upkeep, and, if it is running, supervision time) rather than asking about money alone.
		sch_held, art_held = needs.venture_hands[node_id] if node_id in needs.operating() else (0.0, 0.0)
		if nodes[node_id]["up"] <= 0 and sch_held <= 0.005 and art_held <= 0.005:
			return False, Refusal("nothing_to_save", "that has no money upkeep of yours to stop paying, and "
			                      "nobody of yours is tied up supervising it either; "
			                      "there is nothing to save")
		# A DELIBERATE SHUTDOWN IS NOT AN ABANDONMENT: never_abandon exists to stop the ENGINE quietly deleting a step a
		# player needs and then refusing to fund rebuilding it. A player choosing to close something down is the opposite -
		# they chose it, and restore brings it back. Blocking this here would leave upkeep that is bankrupting a player as
		# the one thing they are not allowed to stop paying for, turning a bad year into an unrecoverable softlock.
		# Knowledge still cannot be unlearned; a building can always be shut.
		if needs.never_abandon[node_id] and needs.category_trait(nodes[node_id]["cat"], "never_abandoned"):
			return False, ("that is knowledge, or it is who you are here. "
			               "You cannot un-know a thing to save its upkeep")
		# SHUTTING A SHOP DOWN IS NOT FORGETTING HOW IT WORKED: this touches only `operating` (what you run), never `done`
		# (what you know). Conflating them would cost a closed loss-maker its place in the tree.
		was_running = node_id in needs.operating()
		earned = needs.venture_real_earnings(node_id) if was_running else 0.0
		self.close_work(node_id, self.CLOSED_BY_CHOICE)
		if not was_running:
			return True, ("%s was not running, so there was nothing to stop "
			              "paying for. You still know how to do it." % node_id)
		# SAY WHAT WAS ACTUALLY FREED, not only the money: a concern held together by staff time alone is reachable by this
		# method, so the confirmation has to say so, or freeing 0.75 craftsmen would read as a no-op that happened to
		# succeed.
		_freed = []
		if nodes[node_id]["up"] > 0 or nodes[node_id]["rev"] > 0:
			_freed.append("you stop paying %s a year for it and stop earning "
			              "the %s a year it brought in"
			              % (needs.money_text(needs.venture_real_upkeep(node_id), grouped=True),
			                 needs.money_text(earned, grouped=True)))
		if sch_held > 0.005 or art_held > 0.005:
			_freed.append("it frees %.2f scholars and %.2f craftsmen who were "
			              "tied up supervising it" % (sch_held, art_held))
		return True, ("%s shut down: %s. You still know how to do it; 'open %s' "
		              "or 'restore %s' opens it again for %s"
		              % (node_id, "; ".join(_freed), node_id, node_id,
		                 needs.money_text(needs.reopen_fee(node_id), grouped=True)))

	def restore_work(self, node_id):
		"""Bring a mothballed work back, and open its doors again.

		A concern costs what `open` quotes for it; any other work costs a share of building it again."""
		needs = self.needs
		if node_id not in needs.mothballed():
			return False, "you have not shut that down"
		if node_id not in needs.techniques_held():
			return False, ('you no longer know how to do that, so there is '
			               'nothing to reopen: build it again with '
			               '{"cmd":"start","id":"%s"}' % node_id)
		gate_refusal = self.running_gate_refusal(node_id)
		if gate_refusal:
			return False, gate_refusal
		node = needs.tree_nodes()[node_id]
		# `open` quotes the same price for a concern.
		fee = needs.reopen_fee(node_id)
		_age = self.staff_closure_age(node_id)
		_in_grace = within_grace(_age, STAFF_CLOSURE_GRACE)
		# SAY WHICH CASE THIS IS, not just a number: the closing message promises a discount inside the window, so a
		# player billed the full price after it needs a line saying the window is gone.
		_grace_note = grace_note(_age, STAFF_CLOSURE_GRACE)
		if fee > needs.spending_power("buy"):
			return False, ("bringing it back costs %s%s, and between "
			               "%s in cash and what anyone will advance against a "
			               "purchase you can raise %s"
			               % (needs.money_text(fee, grouped=True),
			                  ("; " + _grace_note) if _grace_note else "",
			                  needs.money_text(needs.acting_balance(), grouped=True),
			                  needs.money_text(needs.spending_power("buy"), grouped=True)))
		if any(prereq_id not in needs.techniques_held() for prereq_id in node["pre"]):
			return False, ("you no longer have what it stands on: "
			               + ", ".join(prereq_id for prereq_id in node["pre"] if prereq_id not in needs.techniques_held()))
		needs.send(PayEdge(edges.EDGE_WORKERS, fee, "known technique restored"))
		needs.send(LearnTechnique(node_id))
		# Back in service means back in OPERATION: restore is what a player types to reopen something they shut, so a
		# concern goes back on the books; any other work just stops being shut.
		if needs.is_venture[node_id]:
			needs.send(RestoreConcern(node_id))
			needs.send(NoteConcernChange("opening", node_id, "restored", node["rev"], node["up"]))
		else:
			needs.send(CloseConcern(node_id))
		return True, LogLine("restored", "%s back in service for %s%s"
		                     % (node_id, needs.money_text(fee, grouped=True),
		                        (" (%s)" % _grace_note) if _grace_note else ""),
		                     work=node_id, fee=fee, closure_age=_age, discounted=bool(_in_grace))

"""Every reason a project cannot begin, in the order the gate reads them: the list `why`, `stuck`, `available` and
the `start` refusal read, so a readout cannot disagree with the gate (blocker_rules.py)."""
from typing import Any, Dict, List, Optional

from . import blocker_rules


class BlockerViews:
	def start_blockers(self, node_id: str, extra_owed: float = 0.0) -> List[Dict[str, Any]]:
		"""Every reason the project cannot begin now, in gate order; [] when it can. Changes no state. `extra_owed` is
		money already committed by starts not yet applied (a preview's earlier picks)."""
		node = self.needs.tree[node_id]
		if node is None:
			return [{"kind": "unavailable", "cause": "no_such_node", "ids": [], "text": "no such node"}]
		return blocker_rules.collect_blockers(
			self.START_CHECKS + (blocker_rules.EXTENSION_CHECK,),
			lambda check: self.run_check(check, node_id, node, False, None, True),
			lambda check, text: self._classify(check, node_id, node, text),
			lambda: self.money_refusal(node_id, extra_owed))

	def start_refusal(self, node_id: str, extra_owed: float = 0.0) -> Optional[str]:
		"""Why the project cannot begin now, or None. The first entry of `start_blockers`, so the refusal and every
		readout that lists blockers are one function."""
		blockers = self.needs.start_blockers(node_id, extra_owed)
		return blockers[0]["text"] if blockers else None

	def _visible(self, node_id: str) -> bool:
		return self.needs.visible_to_player(node_id)

	def _is_power_capability(self, node_id: str) -> bool:
		return "power_tier" in ((self.needs.tree[node_id] or {}).get("mechanics") or {})

	def _missing_prereq_entries(self, node_id: str, node: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
		done = self.needs.techniques_held()
		missing = [prereq_id for prereq_id in node["pre"] if prereq_id not in done and self._visible(prereq_id)]
		hidden_missing = any(prereq_id not in done and not self._visible(prereq_id) for prereq_id in node["pre"])
		return blocker_rules.missing_prereq_entries(
			missing, hidden_missing, self._is_power_capability, text,
			lambda plain_ids: self.needs.prerequisite_message(plain_ids, None),
			lambda power_ids: blocker_rules.power_gate_text(power_ids, self.needs.generation()))

	def _classify(self, check: blocker_rules.StartCheck, node_id: str, node: Dict[str, Any], text: Any) -> List[Dict[str, Any]]:
		if check.cause == "missing_prereqs":
			return self._missing_prereq_entries(node_id, node, text)
		ids: List[str] = []
		if check.kind == "supply" and check.cause not in blocker_rules.OWN_SUPPLY_IDS:
			_group, options = self.last_substitution_gap() or (None, [])
			ids = [option for option in options if self._visible(option)]
		shut_text = None
		if self.needs.is_venture[node_id] and not self.needs.running[node_id]:
			shut_text = "you have built it already but it is shut: 'open %s' to run it" % node_id
		return [blocker_rules.classify_plain_check(check.cause, check.kind, text, ids, shut_text,
		                                           node_id in self.needs.mothballed())]

"""Fog leak 3: `bounty` named hidden prerequisites outright where `why` correctly said only "N other things you have not
heard of yet", because `bounty` built its own missing-prerequisites list with no fog filter. There is now one filter,
`missing_prereq_message`, and `bounty_refusal` calls it. Rules, each called on built inputs (a fogged stub
with a tree of a few nodes, no game):

1. `missing_prereq_message` prints no id the player has not heard of, and says "have not heard of" instead.
2. `bounty_refusal` returns exactly that message for the same missing list, and refuses an active never-eligible node
   for ineligibility, not with advice to "stop it first".
3. The typed parser reads `reverse:true`, `failures:true` and the bare-flag words of `log` as flags, not as subjects.

Every other command's fog filter is its own (the filters are not central); the pointer scan is test_command_pointer_scan."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.knowledge.api import missing_prereq_message
from sim.refusal import cause_of
from sim.ui.proto.quote_spending import bounty_refusal
from sim.ui.protocol import parse_typed
from sim.tests.ui_stand_in import Game
from sim.tests.ui_stand_in import FactViews

NODES = {
	"target": {"id": "target", "name": "Target", "pre": ["seen_prereq", "hidden_prereq_a", "hidden_prereq_b"],
	           "cat": "metallurgy", "kind": "ENGINEERING"},
	"seen_prereq": {"id": "seen_prereq", "name": "Seen", "pre": [], "cat": "metallurgy", "kind": "ENGINEERING",
	                "ph": 100, "yrs": 1, "risk": 0.1},
	"hidden_prereq_a": {"id": "hidden_prereq_a", "name": "Hidden A", "pre": [], "cat": "metallurgy", "kind": "SCIENCE",
	                    "ph": 100, "yrs": 1, "risk": 0.1},
	"hidden_prereq_b": {"id": "hidden_prereq_b", "name": "Hidden B", "pre": [], "cat": "metallurgy", "kind": "SCIENCE",
	                    "ph": 100, "yrs": 1, "risk": 0.1},
	"never_eligible": {"id": "never_eligible", "name": "Theory", "pre": [], "cat": "science"},
}
HIDDEN = ("hidden_prereq_a", "hidden_prereq_b")


class FoggedStub(FactViews):
	"""A fogged founder who has heard of every node but the two hidden prerequisites."""

	civ = {"name": "Stubland"}

	def __init__(self, fog=True):
		self.nodes = NODES
		self.state = Game(_fog=fog, projects=Game(done=set(), active={}, revealed=set()))
		self.done = self.state.projects.done
		self.active = self.state.projects.active

	def is_visible(self, node_id, _memo=None):
		return not self.state._fog or node_id not in HIDDEN

	def missing_prereq_message(self, missing, _memo=None):
		return missing_prereq_message(self.nodes, missing, self.is_visible, self.state._fog, self.state.projects.done)

	def bounty_eligible(self, node_id):
		return False


class MissingPrerequisiteMessageTests(unittest.TestCase):
	def test_no_id_the_player_has_not_heard_of_is_printed(self):
		message = FoggedStub().missing_prereq_message(list(NODES["target"]["pre"]))
		for hidden_id in HIDDEN:
			self.assertNotIn(hidden_id, message)
		self.assertIn("seen_prereq", message)

	def test_the_hidden_ones_are_counted_in_words(self):
		message = FoggedStub().missing_prereq_message(list(NODES["target"]["pre"]))
		self.assertIn("2 other things you have not heard of", message)  # presentation: the fog sentence the player reads

	def test_without_fog_every_missing_id_is_named(self):
		message = FoggedStub(fog=False).missing_prereq_message(list(NODES["target"]["pre"]))
		for node_id in NODES["target"]["pre"]:
			self.assertIn(node_id, message)

	def test_nothing_missing_is_no_message(self):
		self.assertIsNone(FoggedStub().missing_prereq_message([]))


class BountyRefusalTests(unittest.TestCase):
	def test_bounty_prints_the_one_fog_filtered_message_for_the_same_missing_list(self):
		stub = FoggedStub()
		refusal = bounty_refusal(stub, NODES, "target")
		self.assertEqual(refusal, stub.missing_prereq_message(list(NODES["target"]["pre"])))
		for hidden_id in HIDDEN:
			self.assertNotIn(hidden_id, refusal)

	def test_an_active_never_eligible_node_is_refused_for_ineligibility_not_told_to_stop_it(self):
		stub = FoggedStub()
		stub.active["never_eligible"] = {}
		refusal = bounty_refusal(stub, NODES, "never_eligible")
		self.assertEqual(cause_of(refusal), "not_bounty_eligible")


class BareFlagParsingTests(unittest.TestCase):
	def parsed(self, text):
		return parse_typed(text)[0]

	def test_reverse_true_is_the_boolean_flag_not_a_search_subject(self):
		self.assertEqual(self.parsed("available sort:risk reverse:true"),
		                 {"cmd": "available", "sort": "risk", "reverse": True})

	def test_reverse_true_alone_still_works(self):
		self.assertEqual(self.parsed("available reverse:true"), {"cmd": "available", "reverse": True})

	def test_reverse_false_leaves_it_off(self):
		self.assertEqual(self.parsed("available reverse:false"), {"cmd": "available"})

	def test_log_failures_true_sets_the_flag(self):
		self.assertEqual(self.parsed("log failures:true"), {"cmd": "log", "failures": True})

	def test_log_oldest_true_sets_the_order(self):
		self.assertEqual(self.parsed("log oldest:true").get("order"), "oldest")


if __name__ == "__main__":
	unittest.main()

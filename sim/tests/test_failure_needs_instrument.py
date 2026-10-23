"""Complaint 274: a failure you cannot measure teaches nothing, and says so.

A node that declares `diagnosis_instrument` lets its failures improve the retry odds only when the instrument is held;
the failure report names the figure needed and, without the instrument, which instrument would measure it.

Rules, called on a stub game: `failure_diagnosis.failure_teaches` and `note_failure`. The tree's data (the instrument is
not a prerequisite, so it can be lacked) is read as data. That `_fail_attempt` learns only from
a failure that teaches is in test_failure_charge_rules; the learning itself is test_industry_depth."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.engine.data import closure
from sim.engine.failure_diagnosis import SHORTFALL_FACTOR_RANGE, failure_teaches, note_failure
from sim.tests.harness import NODES

NODE_ID = "cap_tol_1um"
SPEC = NODES[NODE_ID]["mechanics"]["diagnosis_instrument"]
INSTRUMENT = SPEC["instrument"]


class StubGame:
	"""The few things the diagnosis reads: the node's mechanics, the nodes, what is done, and a random stream."""

	def __init__(self, holds_instrument):
		self.nodes = NODES
		self.rng = random.Random(1)
		self.state = SimpleNamespace(projects=SimpleNamespace(done={INSTRUMENT} if holds_instrument else set()))

	def mechanic(self, node_id, name):
		return (NODES[node_id].get("mechanics") or {}).get(name)


class FailureNeedsInstrumentTests(unittest.TestCase):
	def test_the_instrument_is_not_a_prerequisite_so_it_can_be_lacked(self):
		self.assertNotIn(INSTRUMENT, closure(NODES, NODE_ID))

	def test_without_the_instrument_the_failure_teaches_nothing(self):
		self.assertFalse(failure_teaches(StubGame(False), NODE_ID))

	def test_with_the_instrument_the_failure_teaches(self):
		self.assertTrue(failure_teaches(StubGame(True), NODE_ID))

	def test_the_blind_failure_names_the_instrument_and_the_figure_needed_and_says_it_cannot_be_diagnosed(self):
		text = note_failure(StubGame(False), NODE_ID)
		self.assertIn(NODES[INSTRUMENT]["name"], text)  # presentation: the sentence names the instrument
		self.assertIn(SPEC["needed_words"], text)  # presentation: the sentence states the figure the work needed
		self.assertIn("cannot", text)  # presentation: the sentence says it cannot be diagnosed

	def test_the_equipped_failure_reports_what_was_reached_against_what_was_needed(self):
		text = note_failure(StubGame(True), NODE_ID)
		self.assertIn(SPEC["needed_words"], text)  # presentation: the failure line's wording
		self.assertIn("reached", text)  # presentation: the failure line's wording

	def test_the_reported_shortfall_lies_in_the_declared_range(self):
		low, high = SHORTFALL_FACTOR_RANGE
		for seed in range(20):
			game = StubGame(True)
			game.rng = random.Random(seed)
			text = note_failure(game, NODE_ID)
			reached = float(text.split("reached ")[1].split(" ")[0])  # presentation: reads the figure out of the sentence
			self.assertGreaterEqual(reached, SPEC["needed"] * low * 0.999)
			self.assertLessEqual(reached, SPEC["needed"] * high * 1.001)

	def test_a_node_without_the_mechanic_always_teaches_and_adds_no_sentence(self):
		other = next(node_id for node_id, node in NODES.items() if "diagnosis_instrument" not in (node.get("mechanics") or {}))
		for holds in (False, True):
			game = StubGame(holds)
			self.assertTrue(failure_teaches(game, other))
			self.assertEqual(note_failure(game, other), "")


if __name__ == "__main__":
	unittest.main()

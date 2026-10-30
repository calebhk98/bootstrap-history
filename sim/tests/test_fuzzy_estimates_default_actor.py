"""Whose estimate a fuzzy figure is when no actor is named: the player (sim/engine/fuzzy_estimates.py)."""
import unittest

from sim.engine.fuzzy_estimates import DEFAULT_ACTOR, actor_of

QUICK_TOPIC = True


class DefaultActor(unittest.TestCase):

	def test_no_actor_named_is_the_player(self):
		self.assertEqual(actor_of(object()), DEFAULT_ACTOR)

	def test_a_named_actor_is_kept(self):
		self.assertEqual(actor_of(object(), "firm:3"), "firm:3")


if __name__ == "__main__":
	unittest.main()

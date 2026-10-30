"""`narrowed`: the world a mod's actor is handed answers the members the `World` protocol names and refuses every other,
with the caller's error. Called on plain stand-ins, no game."""
QUICK_TOPIC = True

import unittest

from sim.agents.narrowed_world import narrowed, world_surface


class Refused(AttributeError):
	def __init__(self, name):
		super().__init__(name)
		self.name = name


class Inner:
	module = "the actors module"
	year = 1300

	def edge(self, name):
		return "edge " + name

	def rng_for(self, *parts):
		return parts


class NarrowedWorldTests(unittest.TestCase):
	def test_a_protocol_member_answers_as_the_world_does(self):
		world = narrowed(Inner(), Refused)
		self.assertEqual((world.edge("thieves"), world.rng_for(1, "x"), world.year), ("edge thieves", (1, "x"), 1300))

	def test_a_member_the_protocol_does_not_name_is_refused_with_the_callers_error_naming_it(self):
		world = narrowed(Inner(), Refused)
		with self.assertRaises(Refused) as caught:
			world.module
		self.assertEqual(caught.exception.name, "module")

	def test_a_private_member_is_refused(self):
		with self.assertRaises(Refused):
			narrowed(Inner(), Refused)._inner_of_nothing

	def test_a_world_already_narrowed_is_not_narrowed_twice(self):
		world = narrowed(Inner(), Refused)
		self.assertIs(narrowed(world, ValueError), world)

	def test_the_surface_holds_what_actors_ask_and_not_the_engine_handles(self):
		surface = world_surface()
		self.assertTrue({"edge", "rng_for", "year", "land_rent_per_hectare", "market_rate"} <= surface)
		self.assertFalse({"module", "needs", "registry"} & surface)


if __name__ == "__main__":
	unittest.main()

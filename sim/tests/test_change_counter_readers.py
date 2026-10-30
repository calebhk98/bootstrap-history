"""The memo keys that read the owners' change counters move when a counter moves: the polity reach key, the markets category key,
the production epoch of the techniques in use and the stamp of what is running. Each is one function called over plain views."""
QUICK_TOPIC = True

import unittest

from sim.markets.module import Markets
from sim.tests import module_harness, polity_host, production_host


class Counters:
	"""Stand-ins for the owners' views: change one, and the key a reader builds must change."""

	def __init__(self):
		self.values = {"techniques_version": 0, "operating_version": 0, "institution_units_version": 0}

	def views(self):
		return {name: (lambda name=name: self.values[name]) for name in self.values}


def keys_after_each_change(key_of, names):
	"""For each counter in `names`: the key before and after that counter alone moves."""
	moves = {}
	for name in names:
		counters = Counters()
		key_of_now = key_of(counters)
		before = key_of_now()
		counters.values[name] += 1
		moves[name] = (before, key_of_now())
	return moves


class ReachKeyTests(unittest.TestCase):
	def test_the_reach_key_moves_with_the_techniques_and_with_what_is_operating(self):
		def key_of(counters):
			module = polity_host.build(population_total=1000.0, **counters.views())
			return lambda: module._reach_key(0.0)
		for name, (before, after) in keys_after_each_change(key_of, ("techniques_version", "operating_version")).items():
			self.assertNotEqual(before, after, name)

	def test_the_reach_key_ignores_the_institution_sizes(self):
		def key_of(counters):
			module = polity_host.build(population_total=1000.0, **counters.views())
			return lambda: module._reach_key(0.0)
		before, after = keys_after_each_change(key_of, ("institution_units_version",))["institution_units_version"]
		self.assertEqual(before, after)


class CategoryKeyTests(unittest.TestCase):
	def test_the_category_key_moves_with_the_techniques_and_with_what_is_operating(self):
		def key_of(counters):
			module = module_harness.build(Markets, views=dict(
				{"year": 100, "pop_scale": 1.0, "real_output_per_head": 1.0, "concern_versions": (0, 0)}, **counters.views()))
			return module._category_key
		for name, (before, after) in keys_after_each_change(key_of, ("techniques_version", "operating_version")).items():
			self.assertNotEqual(before, after, name)


class ProductionEpochTests(unittest.TestCase):
	def test_the_techniques_epoch_moves_with_the_techniques_and_with_what_is_operating(self):
		def key_of(counters):
			module = production_host.build(**counters.views())
			return module.techniques_epoch
		for name, (before, after) in keys_after_each_change(key_of, ("techniques_version", "operating_version")).items():
			self.assertNotEqual(before, after, name)

	def test_the_running_stamp_moves_with_the_techniques_and_with_what_is_operating(self):
		def key_of(counters):
			module = production_host.build(**counters.views())
			return lambda: module.running_stamp()[1]
		for name, (before, after) in keys_after_each_change(key_of, ("techniques_version", "operating_version")).items():
			self.assertNotEqual(before, after, name)


if __name__ == "__main__":
	unittest.main()

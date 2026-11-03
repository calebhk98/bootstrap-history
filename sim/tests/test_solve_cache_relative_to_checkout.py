"""`solve_cache.relative_to_checkout` names a path inside the checkout relative to it and leaves any other text alone."""
QUICK_TOPIC = True

import os
import unittest

from sim.prices import solve_cache


class RelativeToCheckout(unittest.TestCase):
	def test_a_path_inside_the_checkout_loses_the_checkout(self):
		inside = os.path.join(solve_cache._ROOT, "data", "x.json")
		self.assertEqual(solve_cache.relative_to_checkout(inside), os.path.join("data", "x.json"))

	def test_other_text_is_unchanged(self):
		self.assertEqual(solve_cache.relative_to_checkout("wheat"), "wheat")
		self.assertEqual(solve_cache.relative_to_checkout("/elsewhere/x"), "/elsewhere/x")


if __name__ == "__main__":
	unittest.main()

"""The hand-built three-tile economy opens, steps and conserves money and goods, fast."""
import time
import unittest

from sim.tests import economy_fixture


class FixtureTests(unittest.TestCase):
    def test_it_steps_and_conserves(self):
        started = time.process_time()
        economy, outcomes = economy_fixture.run(years=5)
        self.assertEqual(len(outcomes), 5)
        self.assertLess(time.process_time() - started, 5.0)
        residual = economy.record.book.check_conservation(1e-6)
        self.assertEqual(residual.breaches, ())


if __name__ == "__main__":
    unittest.main()

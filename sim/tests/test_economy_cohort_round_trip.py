QUICK_TOPIC = True

import json
import unittest

from sim.economy.households_cohort import Cohort
from sim.economy.record_plain import plain


class CohortRoundTripTest(unittest.TestCase):
    def test_a_cohort_read_back_from_json_equals_the_cohort_saved(self):
        cohort = Cohort("household:a:0", "a", 0, 10.0, 6.0, 0.2, milled_grains=("barley_kg", "wheat_kg"))
        loaded = Cohort(**json.loads(json.dumps(plain(cohort))))
        self.assertEqual(loaded, cohort)
        self.assertEqual(loaded.milled_grains, ("barley_kg", "wheat_kg"))


if __name__ == "__main__":
    unittest.main()

"""A shipped opening is read under the spin-up's own cache key and stands in for the spin-up; a key with no
shipped record runs the spin-up as before."""
QUICK_TOPIC = True

import json
import os
import tempfile
import unittest
from unittest import mock

from sim.engine import economy_port_year, shipped_openings, shipped_openings_build


class ShippedRecordTests(unittest.TestCase):
    def test_a_written_record_reads_back_as_the_cache_would_return_it(self):
        record = {"producers": {"b": 0.1, "a": [1.5e-300, 3]}, "year": 0}
        with tempfile.TemporaryDirectory() as directory:
            shipped_openings.write("k1", record, directory)
            self.assertEqual(shipped_openings.read("k1", directory), json.loads(json.dumps(record)))
            self.assertIsNone(shipped_openings.read("other", directory))
            self.assertEqual(shipped_openings.shipped_keys(directory), ["k1"])

    def test_the_shipped_record_replaces_the_spin_up_and_a_missing_one_does_not(self):
        economy = mock.Mock()
        economy._spun_up.return_value = {"spun": True}
        with tempfile.TemporaryDirectory() as directory:
            shipped_openings.write("k1", {"shipped": True}, directory)
            with mock.patch.object(shipped_openings, "SHIPPED_OPENINGS_DIRECTORY", directory):
                shipped = economy_port_year.AgentEconomy._shipped_or_spun_up(economy, "k1", "setup")
                computed = economy_port_year.AgentEconomy._shipped_or_spun_up(economy, "k2", "setup")
        self.assertEqual(shipped, {"shipped": True})
        self.assertEqual(computed, {"spun": True})
        economy._spun_up.assert_called_once_with("setup")

    def test_a_shortened_spin_up_is_never_shipped(self):
        with mock.patch.dict(os.environ, {economy_port_year.SPIN_UP_YEARS_ENV: "3,2"}):
            with self.assertRaises(SystemExit):
                shipped_openings_build.build("rome_100ad")


if __name__ == "__main__":
    unittest.main()

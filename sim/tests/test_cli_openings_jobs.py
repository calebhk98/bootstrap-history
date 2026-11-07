"""`openings` builds one civilisation per process up to the machine's cores, and a refused opening is reported with its
reason instead of stopping the others."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.ui import cli_openings


class OpeningsJobsTests(unittest.TestCase):
    def test_one_job_per_civilisation_up_to_the_cores(self):
        with mock.patch.object(cli_openings.os, "cpu_count", lambda: 4):
            self.assertEqual(cli_openings.default_jobs(5), 4)
            self.assertEqual(cli_openings.default_jobs(2), 2)
        with mock.patch.object(cli_openings.os, "cpu_count", lambda: None):
            self.assertEqual(cli_openings.default_jobs(5), 1)

    def test_a_refused_opening_returns_its_reason_and_no_entries(self):
        def refuse(civ_id, before_writing):
            raise SystemExit("%s: not shipped; failing checks: wage_over_floor" % civ_id)
        with mock.patch.object(cli_openings.shipped_openings_build, "build_reporting", refuse):
            civ_id, entries, spin_up, _seconds, refusal = cli_openings.build_one("norse_900ad", None)
        self.assertEqual((civ_id, entries, spin_up), ("norse_900ad", [], None))
        self.assertIn("wage_over_floor", refusal)

    def test_a_shipped_opening_returns_its_entries_and_the_gates(self):
        def build(civ_id, before_writing):
            before_writing.shipped.append(("opening_traces", "trace"))
            return [("agent_economy", "record")], {"settled": False}
        with mock.patch.object(cli_openings.shipped_openings_build, "build_reporting", build):
            _civ, entries, spin_up, _seconds, refusal = cli_openings.build_one("norse_900ad", None)
        self.assertEqual(entries, [("agent_economy", "record"), ("opening_traces", "trace")])
        self.assertEqual((spin_up, refusal), ({"settled": False}, None))


if __name__ == "__main__":
    unittest.main()

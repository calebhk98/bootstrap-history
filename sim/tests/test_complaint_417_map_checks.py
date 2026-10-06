"""Complaint 417: `simulator.py validate` runs the map's own checks, and the burndown lists the map's
heuristic parameters."""

QUICK_TOPIC = True

import contextlib
import io
import unittest
from unittest import mock

from sim import constants
from sim.geography import api as geography
from sim.ui import cli, validate_map


class MapChecksTests(unittest.TestCase):
    def test_validate_reports_a_map_problem_and_fails(self):
        out = io.StringIO()
        with mock.patch.object(validate_map, "problems", return_value=["parameter 'x' lacks a value"]), \
                contextlib.redirect_stdout(out):
            status = cli.cmd_validate(mock.Mock(deep=False))
        self.assertEqual(status, 1)
        self.assertIn("map: parameter 'x' lacks a value", out.getvalue())

    def test_the_installed_maps_are_sound(self):
        self.assertEqual(validate_map.map_problems(), [])

    def test_burndown_lists_the_maps_heuristic_parameters(self):
        listed = constants.burndown()["map_heuristics"]
        self.assertEqual(listed, geography.heuristic_parameters())
        self.assertTrue(listed)


if __name__ == "__main__":
    unittest.main()

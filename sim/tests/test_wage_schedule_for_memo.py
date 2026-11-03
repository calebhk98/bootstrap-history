"""`wage_schedule_for` builds a civilisation record's opening schedule once and serves it again; a variant that keeps the id
is built afresh. The builder is a recorder."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.workforce import views_facts


def facts():
    module = SimpleNamespace(parts=None, clock=None, module_id="workforce", kernels={})
    part = views_facts.FactViews(module)
    part.needs = SimpleNamespace(trade_records=lambda: {})
    return part


class WageScheduleMemoTests(unittest.TestCase):
    def test_the_same_record_is_built_once(self):
        part = facts()
        with mock.patch.object(views_facts, "build_schedule", side_effect=lambda registry, civ: object()) as build:
            first = part.wage_schedule_for({"id": "rome", "population": 1})
            second = part.wage_schedule_for({"id": "rome", "population": 1})
        self.assertIs(first, second)
        self.assertEqual(build.call_count, 1)

    def test_a_variant_keeping_the_id_is_not_served_the_others_schedule(self):
        part = facts()
        with mock.patch.object(views_facts, "build_schedule", side_effect=lambda registry, civ: object()):
            first = part.wage_schedule_for({"id": "rome", "population": 1})
            variant = part.wage_schedule_for({"id": "rome", "population": 2})
        self.assertIsNot(first, variant)


if __name__ == "__main__":
    unittest.main()

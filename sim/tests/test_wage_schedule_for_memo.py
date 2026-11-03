"""The opening schedule of a civilisation record over a trade registry is built once and served again; a variant that keeps the
id, or a different registry, is built afresh. The builder is a recorder."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.workforce import wage_schedule


def build_fresh(registry, civ):
    return object()


class OpeningScheduleMemoTests(unittest.TestCase):
    def test_the_same_record_is_built_once(self):
        with mock.patch.object(wage_schedule, "build_schedule", side_effect=build_fresh) as build:
            registry = {"smith": {}}
            first = wage_schedule.opening_schedule(registry, {"id": "memo_once", "population": 1})
            second = wage_schedule.opening_schedule(dict(registry), {"id": "memo_once", "population": 1})
        self.assertIs(first, second)
        self.assertEqual(build.call_count, 1)

    def test_a_variant_keeping_the_id_is_not_served_the_others_schedule(self):
        with mock.patch.object(wage_schedule, "build_schedule", side_effect=build_fresh):
            first = wage_schedule.opening_schedule({}, {"id": "memo_variant", "population": 1})
            variant = wage_schedule.opening_schedule({}, {"id": "memo_variant", "population": 2})
        self.assertIsNot(first, variant)

    def test_another_registry_is_not_served_the_first_ones_schedule(self):
        with mock.patch.object(wage_schedule, "build_schedule", side_effect=build_fresh):
            civ = {"id": "memo_registry", "population": 1}
            first = wage_schedule.opening_schedule({"smith": {"training_years": 2}}, civ)
            other = wage_schedule.opening_schedule({"smith": {"training_years": 5}}, civ)
        self.assertIsNot(first, other)

    def test_two_variants_alternating_are_each_built_once(self):
        memo, built = wage_schedule.OpeningSchedules(), []

        def build():
            built.append(1)
            return object()
        rome, variant = {"id": "rome", "population": 1}, {"id": "rome", "population": 2}
        first = memo.schedule_for(rome, {}, build)
        other = memo.schedule_for(variant, {}, build)
        self.assertIs(memo.schedule_for(dict(rome), {}, build), first)
        self.assertIs(memo.schedule_for(dict(variant), {}, build), other)
        self.assertEqual(len(built), 2)


if __name__ == "__main__":
    unittest.main()

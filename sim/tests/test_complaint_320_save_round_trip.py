"""Complaint 320: a saved and loaded game plays on exactly as the unbroken one would. State the next year reads must be
in the save: the material demand the last throttle left behind, and the order of every dict (float sums follow it).
The rules are the serialisation of state records (sim/engine/state.py) and the household demand key, called on records
built here. (A whole game saved and loaded: test_scenarios_batch3_saves.)"""
QUICK_TOPIC = True

import json
import unittest

from sim.markets.demand_key import demand_key, population_of_key
from sim.reporting.api import ReportingSeat
from sim.materials.state import MaterialsSeat
from sim.engine.state import HouseholdState, ProjectsState, deserialize_state, serialize_state
from sim.refusal import LogLine, Refusal, cause_of, choices_of, facts_of


def round_trip(record):
    """The record as a save and a load leave it."""
    return deserialize_state(json.loads(json.dumps(serialize_state(record))), type(record))


def shape(entries):
    return [(year, str(message), cause_of(message), facts_of(message), choices_of(message)) for year, message in entries]


def coded_values(value, found, seen):
    """Every Refusal or LogLine held anywhere in a record, as (code, facts)."""
    if id(value) in seen:
        return found
    seen.add(id(value))
    if isinstance(value, Refusal):
        found.append((cause_of(value), facts_of(value)))
    elif isinstance(value, dict):
        for item in list(value.keys()) + list(value.values()):
            coded_values(item, found, seen)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            coded_values(item, found, seen)
    elif hasattr(value, "__dataclass_fields__"):
        for name in value.__dataclass_fields__:
            coded_values(getattr(value, name), found, seen)
    return found


class SavedStateTests(unittest.TestCase):
    def test_a_dict_keeps_its_insertion_order_across_a_save(self):
        order = ["zeta_node", "alpha_node", "mid_node"]
        projects = ProjectsState(done_year={name: number for number, name in enumerate(order)})
        self.assertEqual(list(round_trip(projects).done_year), order)

    def test_the_material_demand_the_last_throttle_left_is_in_the_save(self):
        holdings = MaterialsSeat(material_demand_at_last_throttle={"iron_kg": 3.5, "coal_kg": 1.25})
        self.assertEqual(round_trip(holdings).material_demand_at_last_throttle, {"iron_kg": 3.5, "coal_kg": 1.25})
        self.assertEqual(list(round_trip(holdings).material_demand_at_last_throttle), ["iron_kg", "coal_kg"])

    def test_no_held_demand_stays_none(self):
        self.assertIsNone(round_trip(MaterialsSeat()).material_demand_at_last_throttle)


class LogRoundTripTests(unittest.TestCase):
    @staticmethod
    def household():
        return ReportingSeat(log=[
            (100, LogLine("probe_kind", "a probe line", amount=3, names=["a", "b"])),
            (100, "a plain line"),
            (101, Refusal("probe_cause", "a probe refusal", choices=["x", "y"], figure=2.5))])

    def test_a_log_line_keeps_its_kind_facts_and_choices_across_a_save(self):
        household = self.household()
        self.assertEqual(shape(round_trip(household).log), shape(household.log))

    def test_the_lines_with_a_kind_come_back_with_it(self):
        kinds = [cause_of(message) for _year, message in round_trip(self.household()).log]
        self.assertEqual(kinds, ["probe_kind", None, "probe_cause"])

    def test_the_facts_and_choices_are_the_ones_given(self):
        log = round_trip(self.household()).log
        self.assertEqual(facts_of(log[0][1])["amount"], 3)
        self.assertEqual(facts_of(log[0][1])["names"], ["a", "b"])
        self.assertEqual(choices_of(log[2][1]), ["x", "y"])

    def test_every_coded_value_held_in_the_record_comes_back(self):
        household = self.household()
        again = round_trip(household)
        self.assertEqual(sorted(map(repr, coded_values(again, [], set()))),
                         sorted(map(repr, coded_values(household, [], set()))))
        self.assertEqual(len(coded_values(again, [], set())), 2)


class DemandKeyTests(unittest.TestCase):
    OPENING = 1_000_000.0

    def test_a_population_that_moved_less_than_the_rounding_step_has_the_same_key(self):
        before = demand_key(500_000.0, self.OPENING, 10.0)
        after = demand_key(500_000.0 * 1.0003, self.OPENING, 10.0)
        self.assertEqual(before, after)

    def test_an_income_that_moved_less_than_the_rounding_step_has_the_same_key(self):
        self.assertEqual(demand_key(500_000.0, self.OPENING, 10.0001), demand_key(500_000.0, self.OPENING, 10.0003))

    def test_a_population_that_moved_more_than_a_step_has_another_key(self):
        self.assertNotEqual(demand_key(500_000.0, self.OPENING, 10.0), demand_key(500_000.0 * 1.01, self.OPENING, 10.0))

    def test_the_answer_is_computed_from_the_key_so_it_is_the_same_whenever_it_is_asked(self):
        first = demand_key(500_000.0, self.OPENING, 10.0)
        second = demand_key(500_000.0 * 1.0003, self.OPENING, 10.0)
        self.assertEqual(population_of_key(first, self.OPENING), population_of_key(second, self.OPENING))

    def test_the_key_stands_for_a_population_within_a_step_of_the_real_one(self):
        key = demand_key(512_345.0, self.OPENING, 10.0)
        self.assertLess(abs(population_of_key(key, self.OPENING) - 512_345.0), 0.001 * self.OPENING)


if __name__ == "__main__":
    unittest.main()

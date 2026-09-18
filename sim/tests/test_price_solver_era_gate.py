"""Pins the era gate that Complaints/39 asked for: `sim/solve_prices.py` had
no notion of WHEN, so a 100 AD Roman scenario priced all three of its energy
carriers off a photovoltaic panel. The panel was correct data and the
cheapest source of electricity at solved prices; it was simply not available
to anyone alive in 100 AD, and nothing in the solver could say so.

`techniques_available_to` is the gate. These tests pin the three states a
`requires_node` can be in and, more importantly, the two ways the gate could
be made useless while still looking like it worked:

  - treating an UNCLASSIFIED entry as universally available, which is
    exactly how the panel got into a Roman answer;
  - letting a gated solve quietly fall back to the full technique set when
    the era set happens to be small.

Written as unittest.TestCase against solve_prices directly, like
test_price_solver_cycles.py, so it does not drag in the engine.
"""
import unittest

from sim import solve_prices


def entry(requires_node="__absent__"):
    """A minimal production entry, optionally carrying `requires_node`.

    The sentinel matters: leaving the field OUT is a different state from
    setting it to None, and a test that could not tell them apart would pass
    against a gate that had collapsed the two.
    """
    built = {"outputs": {"thing_kg": 1.0}, "inputs": {},
             "labour_hours": {"labourer": 1.0}}
    if requires_node != "__absent__":
        built["requires_node"] = requires_node
    return built


class EraGateTests(unittest.TestCase):

    def test_the_three_states_are_three_different_answers(self):
        entries = {
            "universal": entry(None),
            "reached": entry("smelting"),
            "not_reached": entry("electrolysis"),
            "unclassified": entry(),
        }
        available, unreached, unclassified = solve_prices.techniques_available_to(
            entries, {"smelting"})
        self.assertEqual(sorted(available), ["reached", "universal"])
        self.assertEqual(unreached, ["not_reached"])
        self.assertEqual(unclassified, ["unclassified"])

    def test_an_unclassified_technique_is_dropped_rather_than_admitted(self):
        # THE WHOLE POINT. An entry that says nothing about when it becomes
        # available is an unanswered question. Admitting it to a gated solve
        # is how a photovoltaic panel priced Roman electricity, and it would
        # do it again: the panel carries no requires_node until someone
        # labels it.
        entries = {"photovoltaic_like": entry()}
        available, _unreached, unclassified = solve_prices.techniques_available_to(
            entries, {"anything"})
        self.assertEqual(available, {})
        self.assertEqual(unclassified, ["photovoltaic_like"])

    def test_an_empty_era_set_admits_only_the_no_technology_techniques(self):
        # A civilization holding nothing at all can still gather firewood.
        # It cannot do anything that names a node, and the gate must not
        # decide that an era set this small means "gating is not worth it".
        entries = {"gathering": entry(None), "smelting": entry("smelting")}
        available, unreached, _unclassified = solve_prices.techniques_available_to(
            entries, set())
        self.assertEqual(sorted(available), ["gathering"])
        self.assertEqual(unreached, ["smelting"])

    def test_the_gate_does_not_mutate_what_it_was_given(self):
        # main() keeps the pre-gate entries to tell "gated out" apart from
        # "no entry at all" in its report, so the gate returning a view that
        # aliased or emptied the original would make that report wrong.
        entries = {"a": entry(None), "b": entry("unreached_node")}
        available, _unreached, _unclassified = solve_prices.techniques_available_to(
            entries, set())
        self.assertEqual(len(entries), 2)
        self.assertIsNot(available, entries)

    def test_rome_holds_a_real_era_set_from_its_own_starting_techs(self):
        # The era set is an INITIAL CONDITION read off the civilization file,
        # not a table of invention dates living in the solver - see
        # CLAUDE.md section 3.1 and the module docstring. This asserts the
        # shape and the source, never a count that authoring would churn.
        reached = solve_prices.load_starting_technologies("rome_100ad")
        self.assertTrue(reached)
        self.assertTrue(all(isinstance(node_id, str) for node_id in reached))

    def test_an_unknown_civilization_names_the_real_ones(self):
        with self.assertRaises(FileNotFoundError) as raised:
            solve_prices.load_starting_technologies("atlantis_9000bc")
        self.assertIn("rome_100ad", str(raised.exception))


if __name__ == "__main__":
    unittest.main()

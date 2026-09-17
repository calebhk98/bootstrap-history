"""Checks the fix for Complaints/31: `sim/solve_prices.py` used to refuse
every recipe cycle, although its own module docstring said cycles were
expected and used one as its worked example. `compute_resolvable_materials`
now runs a strongly-connected-component productiveness test (Hawkins-Simon)
on whatever the plain topological pass cannot reach, instead of refusing it
outright - see the module docstring's CYCLES section and
`_component_is_productive`.

INVERTED FROM THE ORIGINAL PIN ON PURPOSE. This file used to assert the
WRONG answer deliberately, with instructions to flip each assertion once the
pass was fixed rather than delete the test - a red suite gets ignored, a
green one pinning a known defect does not. The pass is fixed now, so these
assert the right answer instead, and stay here as regression coverage for
the same two reproductions.

Written as unittest.TestCase rather than the flat check()-at-import style,
like test_agriculture.py and test_demography.py, so it can exercise
solve_prices directly without dragging in sim/tests/harness.py and the whole
engine behind it.
"""
import unittest

from sim import solve_prices


class ResolvabilityAcceptsProductiveCyclesTests(unittest.TestCase):

    def test_the_docstrings_own_axe_and_iron_example_resolves(self):
        # Timber is extracted (no inputs, labour only), so this system does
        # bottom out. Iron needs a little axe; an axe needs iron. A tiny
        # circulating share like this is productive and the damped iteration
        # already in solve_prices.py converges on it.
        entries = {
            "timber": {"outputs": {"timber_m3": 1.0}, "inputs": {},
                       "labour_hours": {"labourer": 2.0}},
            "iron": {"outputs": {"iron_kg": 10.0},
                     "inputs": {"timber_m3": 1.0, "axe_each": 0.01},
                     "labour_hours": {"labourer": 5.0}},
            "axe": {"outputs": {"axe_each": 1.0}, "inputs": {"iron_kg": 2.0},
                    "labour_hours": {"labourer": 3.0}},
        }
        resolvable = solve_prices.compute_resolvable_materials(
            entries, solve_prices.build_producers_index(entries))

        self.assertEqual(
            resolvable, {"timber_m3", "iron_kg", "axe_each"},
            "compute_resolvable_materials refuses the axe/iron cycle again - "
            "see Complaints/31 and _component_is_productive.")

    def test_a_self_input_resolves_and_so_does_its_consumer(self):
        # Seed corn: the physically correct wheat entry lists wheat among its
        # own inputs and outputs the GROSS yield. 165 of 742.5 is a
        # circulating share of 22%, comfortably productive, and bread
        # downstream of it should resolve too.
        entries = {
            "wheat": {"outputs": {"wheat_kg": 742.5},
                      "inputs": {"wheat_kg": 165.0},
                      "labour_hours": {"labourer": 150.0}},
            "bread": {"outputs": {"bread_kg": 1.0}, "inputs": {"wheat_kg": 1.3},
                      "labour_hours": {"labourer": 0.2}},
        }
        resolvable = solve_prices.compute_resolvable_materials(
            entries, solve_prices.build_producers_index(entries))

        self.assertEqual(
            resolvable, {"wheat_kg", "bread_kg"},
            "a self-input poisons its whole downstream again - see "
            "Complaints/31 and the note in this file's docstring.")

    def test_a_cycle_that_consumes_more_than_it_yields_is_still_refused(self):
        # The strict pass exists for a reason: a cycle whose spectral radius
        # is at or above 1 has no fixed point and must still be named and
        # refused, not handed a floating-point number that looks real.
        entries = {
            "bad": {"outputs": {"bad_kg": 1.0}, "inputs": {"bad_kg": 1.5},
                    "labour_hours": {"labourer": 1.0}},
        }
        diagnostics = []
        resolvable = solve_prices.compute_resolvable_materials(
            entries, solve_prices.build_producers_index(entries),
            diagnostics=diagnostics)

        self.assertEqual(resolvable, set())
        self.assertEqual(len(diagnostics), 1)
        self.assertIn("bad_kg", diagnostics[0])

    def test_a_cycle_with_no_labour_or_extracted_anchor_is_refused(self):
        # A self-loop with nothing else in it at all - no labour, no
        # external material - never bottoms out, so there is nothing to
        # price it from regardless of whether the share is small.
        entries = {
            "ghost": {"outputs": {"ghost_kg": 1.0}, "inputs": {"ghost_kg": 0.5}},
        }
        diagnostics = []
        resolvable = solve_prices.compute_resolvable_materials(
            entries, solve_prices.build_producers_index(entries),
            diagnostics=diagnostics)

        self.assertEqual(resolvable, set())
        self.assertEqual(len(diagnostics), 1)
        self.assertIn("ghost_kg", diagnostics[0])

    def test_the_netted_out_form_the_data_actually_uses_does_resolve(self):
        # This is why the defect is latent rather than breaking the solver
        # today: data/production/40_organics.json states wheat net of seed,
        # with empty inputs, precisely to stay inside what the pass accepts.
        # The entry's own yield_basis says so and points here.
        entries = {
            "wheat": {"outputs": {"wheat_kg": 577.5}, "inputs": {},
                      "labour_hours": {"labourer": 150.0}},
            "bread": {"outputs": {"bread_kg": 1.0}, "inputs": {"wheat_kg": 1.3},
                      "labour_hours": {"labourer": 0.2}},
        }
        resolvable = solve_prices.compute_resolvable_materials(
            entries, solve_prices.build_producers_index(entries))
        self.assertEqual(resolvable, {"wheat_kg", "bread_kg"})

    def test_the_real_dataset_is_currently_acyclic_so_nothing_is_lost_today(self):
        # The claim in Complaints/31 that this is latent rather than active
        # is checked here rather than asserted in prose. If a future
        # production entry introduces a genuine cycle, this fails and names
        # what stopped resolving - which is the moment the pass has to be
        # fixed rather than worked around.
        entries, _duplicates = solve_prices.load_production()
        resolvable = solve_prices.compute_resolvable_materials(
            entries, solve_prices.build_producers_index(entries))
        unresolved = sorted(
            material
            for entry in entries.values()
            for material in (entry.get("outputs") or {})
            if material not in resolvable)
        self.assertEqual(
            unresolved, [],
            "a production entry now has no path to a price. Either it is a "
            "genuine data hole, or it is a cycle that Complaints/31's "
            "resolvability defect is refusing - check which before adding a "
            "workaround.")


if __name__ == "__main__":
    unittest.main()

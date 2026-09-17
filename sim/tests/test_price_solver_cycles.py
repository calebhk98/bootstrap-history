"""Pins the defect in Complaints/31: `sim/solve_prices.py` refuses every
recipe cycle, although its own module docstring says cycles are expected and
uses one as its worked example.

WRITTEN AS A PIN ON THE WRONG BEHAVIOUR, NOT AS A FAILING TEST, deliberately.
A red suite gets ignored; a green suite with an explicit statement of what is
currently wrong does not. Each assertion below says what the code does today
AND what the right answer is, so whoever fixes `compute_resolvable_materials`
finds this file immediately, flips the assertion, and cannot mistake the fix
for a regression. Do not delete these when the pass is fixed - invert them.

Written as unittest.TestCase rather than the flat check()-at-import style,
like test_agriculture.py and test_demography.py, so it can exercise
solve_prices directly without dragging in sim/tests/harness.py and the whole
engine behind it.
"""
import unittest

from sim import solve_prices


class ResolvabilityRejectsCyclesTests(unittest.TestCase):

    def test_the_docstrings_own_axe_and_iron_example_is_refused(self):
        # Timber is extracted (no inputs, labour only), so this system does
        # bottom out. Iron needs a little axe; an axe needs iron. A tiny
        # circulating share like this is productive and the damped iteration
        # already in solve_prices.py would converge on it.
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

        # WRONG, and pinned as wrong: the right answer is all three.
        self.assertEqual(
            resolvable, {"timber_m3"},
            "solve_prices.compute_resolvable_materials no longer refuses the "
            "axe/iron cycle. If that is because someone fixed it - see "
            "Complaints/31 - this assertion should now read {'timber_m3', "
            "'iron_kg', 'axe_each'}, and the two below should be inverted "
            "too. Do not delete them.")

    def test_a_self_input_is_refused_and_takes_its_consumers_with_it(self):
        # Seed corn: the physically correct wheat entry lists wheat among its
        # own inputs and outputs the GROSS yield. The pass refuses it, and
        # because bread needs wheat, bread goes unresolvable too - a single
        # self-loop silently removes an entire downstream branch.
        entries = {
            "wheat": {"outputs": {"wheat_kg": 742.5},
                      "inputs": {"wheat_kg": 165.0},
                      "labour_hours": {"labourer": 150.0}},
            "bread": {"outputs": {"bread_kg": 1.0}, "inputs": {"wheat_kg": 1.3},
                      "labour_hours": {"labourer": 0.2}},
        }
        resolvable = solve_prices.compute_resolvable_materials(
            entries, solve_prices.build_producers_index(entries))

        # WRONG, and pinned as wrong: the right answer is both materials.
        # 165 of 742.5 is a circulating share of 22%, comfortably productive.
        self.assertEqual(
            resolvable, set(),
            "a self-input no longer poisons its whole downstream - see "
            "Complaints/31 and the note in this file's docstring.")

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

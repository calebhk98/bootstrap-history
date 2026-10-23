"""Pins the fix for Complaints/43, in two rounds.

ROUND ONE (the original Complaints/43 incident): England 1300's water wheel
made mechanical_mj roughly 1,347 times cheaper than human muscle, cheap
enough that thermal_mj_friction (a warm bearing, ~98% efficient at turning
shaft work into heat) undercut charcoal for the shared, undifferentiated
thermal_mj carrier - even though thermal_mj_friction's own yield_basis
predicted this could never happen. The fix gave every thermal_mj-supplying
technique a `temperature_reached_c`, gave a specific consumer an optional
`temperature_needed_c`, and computed ONE shared floor for the whole pool -
the larger of the pool's own universal default and whatever the single
hottest active consumer stated it needed.

ROUND TWO (this file's own change, found by the stakeholder reasoning about
round one rather than by running anything): a SINGLE SHARED FLOOR is itself
a bug, in both directions the stakeholder named. Invent a technique that
reaches 2500 C anywhere in the economy and the old mechanism raised the
floor to 2500 C for EVERY thermal_mj consumer, locking a 1100 C charcoal
fire out of firing a brick it could obviously still fire. Make mechanical_mj
suddenly cheap somewhere and the same mechanism let a warm, low-grade source
undercut every hotter use too, because the floor was the only thing
standing between "cheap" and "chosen" and it was shared by every consumer at
once. Both follow from conflating "what the hottest job needs" with "what
every job may use."

THE FIX IS PER-CONSUMER GRADING, not a second global number and not several
separate carrier materials (see TEMPERATURE in sim/engine/solve_prices.py's module
docstring for why a materials-per-band split was rejected specifically
because it would need every OTHER consuming entry - most of them in files
this task does not own - rewritten to name a band rather than the plain
`thermal_mj` field they already use). `capability_required_grades` collects
every distinct requirement this era's own entries actually state, and
`capability_price_for_requirement` solves each one SEPARATELY: the cheapest
technique that clears THAT ONE requirement, at this round's own prices.
`capability_floor_by_carrier` now returns only the carrier's own universal
default - it no longer inspects what any consumer needs - so the "shared
pool" price everything without a stated requirement pays is the one number
that never moves no matter how hot or cold any OTHER consumer's own need
is.

Written as unittest.TestCase against solve_prices directly, like
test_price_solver_era_gate.py and test_price_solver_rent.py: synthetic
entries pin the MECHANISM independent of any future edit to the real data
(which `data/production/` mostly is, owned elsewhere), and a smaller
integration class pins the actual acceptance tests this task was given,
against the real data/production/70_energy.json and
data/civilizations/*.json.

Techniques state the temperature they reach and processes the temperature they need; the cheapest working technique wins.
"""
import unittest

from sim.engine import solve_prices
from sim.tests.price_solver_helpers import engine_solve_converges, solver_context



class RealDataAcceptanceTests(unittest.TestCase):
    """The acceptance tests this task was actually given, against the real
    data/production/70_energy.json and data/civilizations/*.json: England
    1300 must burn a real fuel, not friction, Rome must be unaffected, and
    both civilisations' gated solves must converge - see Complaints/43's
    own before/after numbers and this task's own report for the round-two
    numbers (a synthetic hot consumer added to the real England 1300
    economy leaves plaster_kg's real, converged price untouched).
    """

    def _thermal_choice(self, civilization_id):
        available, wage_by_trade, producers_of, rent = solver_context(
            civilization_id)
        resolvable = solve_prices.compute_resolvable_materials(
            available, producers_of, rent_hours_per_kg_by_material=rent)
        _prices, _iters, _residual, chosen = solve_prices.solve(
            available, producers_of, resolvable, wage_by_trade,
            rent_hours_per_kg_by_material=rent)
        return chosen.get("thermal_mj")

    # Coal is priceable once iron_bar_kg is makeable (its shaft capital draws on bar),
    # so the cheapest real fuel may be either solid fuel; friction must never win.
    REAL_FUELS = ("thermal_mj_charcoal", "thermal_mj_coal")

    def test_england_1300_burns_a_real_fuel_not_friction(self):
        self.assertIn(self._thermal_choice("england_1300"), self.REAL_FUELS)

    def test_rome_100ad_burns_a_real_fuel_not_friction(self):
        self.assertIn(self._thermal_choice("rome_100ad"), self.REAL_FUELS)

    def test_the_ungated_solve_still_converges(self):
        self.assertTrue(engine_solve_converges())

    def test_the_gated_solves_still_converge(self):
        self.assertTrue(engine_solve_converges("england_1300"))
        self.assertTrue(engine_solve_converges("rome_100ad"))

    def _real_data_solve(self, civilization_id, extra_entries=None):
        production_entries, _duplicates = solve_prices.load_production()
        if extra_entries:
            production_entries = dict(production_entries)
            production_entries.update(extra_entries)
        reached = solve_prices.load_starting_technologies(civilization_id)
        available, _unreached, _unclassified = solve_prices.techniques_available_to(
            production_entries, reached)
        from sim import simulator
        _tree, prices_json, _nodes, _wages, _goods = simulator.load()
        wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)
        producers_of = solve_prices.build_producers_index(available)
        rent = solve_prices.rent_hours_per_kg_by_ore_material(available, wage_by_trade)
        resolvable = solve_prices.compute_resolvable_materials(
            available, producers_of, rent_hours_per_kg_by_material=rent)
        return solve_prices.solve(
            available, producers_of, resolvable, wage_by_trade,
            rent_hours_per_kg_by_material=rent)

    def test_a_hypothetical_2500c_consumer_does_not_move_englands_real_plaster_price(self):
        # THE TASK'S OWN ACCEPTANCE SCENARIO, against the REAL England
        # 1300 economy rather than a synthetic one: plaster_kg is a real
        # entry (owned elsewhere) that draws thermal_mj with no stated
        # requirement of its own, so it must be completely insulated from
        # a brand-new, unrelated, 2500 C requirement appearing anywhere
        # else in the same economy.
        prices_before, _iterations, _residual, _chosen = self._real_data_solve("england_1300")
        fusion_entry = {
            "synthetic_fusion_forge": {
                "outputs": {"synthetic_fusion_widget_kg": 1.0}, "inputs": {},
                "labour_hours": {"labourer": 0.001}, "thermal_mj": 1.0,
                "temperature_needed_c": 2500.0, "requires_node": None,
            }
        }
        prices_after, _iterations, _residual, _chosen = self._real_data_solve(
            "england_1300", extra_entries=fusion_entry)
        self.assertEqual(prices_before["plaster_kg"], prices_after["plaster_kg"])
        self.assertEqual(prices_before["thermal_mj"], prices_after["thermal_mj"])


if __name__ == "__main__":
    unittest.main()

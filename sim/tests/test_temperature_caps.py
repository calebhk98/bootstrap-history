"""Pins the fix for Complaints/44: England 1300's water wheel made
mechanical_mj roughly 1,347 times cheaper than human muscle, cheap enough
that thermal_mj_friction (a warm bearing, ~98% efficient at turning shaft
work into heat) undercut charcoal for the shared, undifferentiated
thermal_mj carrier - even though thermal_mj_friction's own yield_basis
predicted this could never happen. `sim/solve_prices.py`'s choice-of-
technique mechanism did exactly what it is defined to do; the defect was
that a megajoule of heat was a megajoule of heat to the solver no matter
what temperature it arrived at, so a warm bearing and a charcoal fire were
interchangeable.

The fix is CAPABILITY_CAP_FIELDS, `temperature_reached_c` on each thermal
technique in data/production/70_energy.json, `temperature_needed_c` for a
specific consumer that needs more than the default, and
THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C (data/tech_tree.json's own free,
universal `cap_heat_0700` rung) as the shared pool's own floor - a general
eligibility test any technique is checked against, not a special case
naming friction. See CAPABILITY_CAP_FIELDS and TEMPERATURE in
sim/solve_prices.py's module docstring for the mechanism in full.

Written as unittest.TestCase against solve_prices directly, like
test_price_solver_era_gate.py and test_price_solver_rent.py: synthetic
entries pin the MECHANISM independent of any future edit to the real data
(which `data/production/` mostly is, owned elsewhere), and a smaller
integration class pins the actual acceptance test this task was given,
against the real data/production/70_energy.json and
data/civilizations/*.json.
"""
import unittest

from sim import solve_prices


class CapabilityFloorByCarrierTests(unittest.TestCase):
    """`capability_floor_by_carrier` in isolation, with tiny synthetic
    entries - independent of what the real data currently says.
    """

    def test_the_default_floor_applies_with_no_active_consumer(self):
        floor = solve_prices.capability_floor_by_carrier({})
        self.assertEqual(floor["thermal_mj"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)

    def test_an_active_consumer_can_raise_the_floor_above_the_default(self):
        entries = {
            "hot_process": {"outputs": {"widget_kg": 1.0}, "inputs": {},
                            "labour_hours": {}, "thermal_mj": 5.0,
                            "temperature_needed_c": 2000.0},
        }
        floor = solve_prices.capability_floor_by_carrier(entries)
        self.assertEqual(floor["thermal_mj"], 2000.0)

    def test_a_stated_need_below_the_default_does_not_lower_it(self):
        # The floor is a MAXIMUM of the default and every stated need - a
        # consumer that would be happy with less never gets to license a
        # lower-grade technique for everyone else sharing the pool.
        entries = {
            "mild_process": {"outputs": {"widget_kg": 1.0}, "inputs": {},
                             "labour_hours": {}, "thermal_mj": 5.0,
                             "temperature_needed_c": 150.0},
        }
        floor = solve_prices.capability_floor_by_carrier(entries)
        self.assertEqual(floor["thermal_mj"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)

    def test_a_consumer_that_does_not_draw_the_carrier_is_ignored(self):
        # A `temperature_needed_c` on an entry with no (or zero) thermal_mj
        # of its own is not "this era needs more heat" - it is not asking
        # for any heat at all, so it must not raise the floor.
        entries = {
            "irrelevant": {"outputs": {"widget_kg": 1.0}, "inputs": {},
                          "labour_hours": {}, "temperature_needed_c": 5000.0},
        }
        floor = solve_prices.capability_floor_by_carrier(entries)
        self.assertEqual(floor["thermal_mj"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)

    def test_a_consumer_with_no_stated_need_does_not_raise_the_floor(self):
        # "No stated requirement" means exactly that, not zero and not
        # "assume the default" restated as a need - see _SCHEMA.md's own
        # WHEN TO ADD A TEMPERATURE REQUIREMENT.
        entries = {
            "unannotated": {"outputs": {"widget_kg": 1.0}, "inputs": {},
                           "labour_hours": {}, "thermal_mj": 5.0},
        }
        floor = solve_prices.capability_floor_by_carrier(entries)
        self.assertEqual(floor["thermal_mj"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)


class SyntheticFrictionScenarioTests(unittest.TestCase):
    """Reproduces the SHAPE of Complaints/44 with tiny synthetic entries: a
    cheap mechanical_mj source (standing in for a water wheel), a friction
    conversion that wins on running cost alone, and a real fuel that costs
    more per MJ but clears the temperature floor. This exercises `solve`
    itself, not just the helper functions above in isolation, so it is a
    canary that the fix is actually wired into the choice-of-technique
    loop rather than merely present in the file.
    """

    def _entries(self, capped):
        entries = {
            "cheap_shaft": {"outputs": {"mechanical_mj": 1000.0}, "inputs": {},
                            "labour_hours": {"labourer": 0.001},
                            "requires_node": None},
            "friction": {"outputs": {"thermal_mj": 1000.0}, "inputs": {},
                        "labour_hours": {}, "mechanical_mj": 1.0,
                        "requires_node": None},
            "real_fuel": {"outputs": {"thermal_mj": 1000.0}, "inputs": {},
                         "labour_hours": {"labourer": 10.0},
                         "requires_node": None},
        }
        if capped:
            entries["friction"]["temperature_reached_c"] = 100.0
            entries["real_fuel"]["temperature_reached_c"] = 1100.0
        return entries

    def _thermal_choice(self, entries):
        wage_by_trade = {"labourer": 1.0}
        producers_of = solve_prices.build_producers_index(entries)
        resolvable = solve_prices.compute_resolvable_materials(entries, producers_of)
        _prices, _iters, _residual, chosen = solve_prices.solve(
            entries, producers_of, resolvable, wage_by_trade)
        return chosen["thermal_mj"]

    def test_without_any_stated_reach_friction_wins_on_cost_alone(self):
        # Pins the OLD behaviour on these synthetic entries, so the next
        # test's result is legible as "the cap changed this", not "these
        # entries never exercised the choice to begin with".
        self.assertEqual(self._thermal_choice(self._entries(capped=False)), "friction")

    def test_with_a_stated_reach_the_real_fuel_wins_instead(self):
        self.assertEqual(self._thermal_choice(self._entries(capped=True)), "real_fuel")


class RealDataAcceptanceTests(unittest.TestCase):
    """The acceptance test this task was actually given, against the real
    data/production/70_energy.json and data/civilizations/*.json: England
    1300 must burn a real fuel, not friction, and Rome must be unaffected -
    see Complaints/44's own before/after numbers.
    """

    def _thermal_choice(self, civilization_id):
        production_entries, _duplicates = solve_prices.load_production()
        reached = solve_prices.load_starting_technologies(civilization_id)
        available, _unreached, _unclassified = solve_prices.techniques_available_to(
            production_entries, reached)
        import simulator
        _tree, prices_json, _nodes, _wages, _goods = simulator.load()
        wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)
        producers_of = solve_prices.build_producers_index(available)
        rent = solve_prices.rent_hours_per_kg_by_ore_material(available, wage_by_trade)
        resolvable = solve_prices.compute_resolvable_materials(
            available, producers_of, rent_hours_per_kg_by_material=rent)
        _prices, _iters, _residual, chosen = solve_prices.solve(
            available, producers_of, resolvable, wage_by_trade,
            rent_hours_per_kg_by_material=rent)
        return chosen.get("thermal_mj")

    def test_england_1300_burns_a_real_fuel_not_friction(self):
        self.assertEqual(self._thermal_choice("england_1300"), "thermal_mj_charcoal")

    def test_rome_100ad_still_burns_charcoal(self):
        self.assertEqual(self._thermal_choice("rome_100ad"), "thermal_mj_charcoal")

    def test_thermal_mj_friction_cannot_clear_the_universal_floor(self):
        # The physical fact this whole fix rests on: friction's own stated
        # reach (an open, unpressurised heater's ceiling - see that
        # entry's own yield_basis) is below the tree's own free starting
        # heat rung, cap_heat_0700.
        production_entries, _duplicates = solve_prices.load_production()
        friction = production_entries["thermal_mj_friction"]
        self.assertLess(friction["temperature_reached_c"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)

    def test_charcoal_and_coal_clear_the_universal_floor(self):
        production_entries, _duplicates = solve_prices.load_production()
        for recipe_id in ("thermal_mj_charcoal", "thermal_mj_coal"):
            self.assertGreaterEqual(
                production_entries[recipe_id]["temperature_reached_c"],
                solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)

    def test_the_ungated_solve_still_converges(self):
        self.assertEqual(solve_prices.main([]), 0)

    def test_the_gated_solves_still_converge(self):
        self.assertEqual(solve_prices.main(["--civ", "england_1300"]), 0)
        self.assertEqual(solve_prices.main(["--civ", "rome_100ad"]), 0)


if __name__ == "__main__":
    unittest.main()

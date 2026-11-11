"""`solve_prices_core.solve` (undamped opening rounds, then damped) set against the solver as it was (damped from the first round,
`price_solve_reference.reference_solve`) on the inputs of four years of a Rome game (`price_solve_rome_inputs.json`: the techniques
reached, the wages, the rents, the market rate) and on random variations of them. The prices agree within the engine's own stopping
tolerance, a material is priced the same way (made or not), and a material whose cheapest technique differs is a tie between
two techniques. The new solve needs fewer rounds."""

import json
import os
import random
import unittest

from sim.prices import disposal_cost, engine_seam, prices, solve_prices_core, solve_prices_round
from sim.prices.price_change import relative_price_change
from sim.tests import price_solve_reference

ENGINE_TOLERANCE = prices.ENGINE_SOLVE_TOLERANCE
TIE_TOLERANCE = 1e-6
DUST_HOURS_PER_UNIT = 1e-6    # a price this small is a waste that costs nothing: the old solve left it at its last halving, the new one at the smallest price told from zero
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "price_solve_rome_inputs.json")


def prepared(entries_by_key, wages, rent, rate):
    producers_of = solve_prices_core.build_producers_index(entries_by_key)
    resolvable = solve_prices_core.compute_resolvable_materials(
        entries_by_key, producers_of, rent_hours_per_kg_by_material=rent)
    return producers_of, resolvable


def both_solves(entries_by_key, wages, rent, rate, dump):
    producers_of, resolvable = prepared(entries_by_key, wages, rent, rate)
    arguments = dict(rent_hours_per_kg_by_material=rent, interest_rate=rate, dump_minimum_distance_kilometres=dump,
                     tolerance=ENGINE_TOLERANCE)
    new = solve_prices_core.solve(entries_by_key, producers_of, set(resolvable), wages, **arguments)
    old = price_solve_reference.reference_solve(entries_by_key, producers_of, set(resolvable), wages, **arguments)
    return new, old


def cheapest_price_of(entries_by_key, wages, rent, rate, dump, prices_now, material, recipe_id):
    """What `recipe_id` would price `material` at, given `prices_now`; None if it cannot be costed."""
    producers_of = solve_prices_core.build_producers_index(entries_by_key)
    resolvable = set(prices_now)
    floor_by_carrier = solve_prices_core.capability_floor_by_carrier()
    plans = solve_prices_round.build_plans(entries_by_key, sorted(entries_by_key), resolvable, wages, rent, rate, floor_by_carrier)
    grades = solve_prices_core.capability_required_grades(entries_by_key)
    bands = solve_prices_round.band_prices(grades, solve_prices_round.band_suppliers(grades, entries_by_key), prices_now, wages,
                                           rent, rate, dump)
    disposal = disposal_cost.disposal_cost_by_material(disposal_cost.joint_output_materials(entries_by_key), prices_now, rate, dump)
    candidates = solve_prices_round.round_candidates(plans, prices_now, wages, bands, rate, disposal)
    return {recipe: price for price, recipe in candidates.get(material, ())}.get(recipe_id)


def compare(entries_by_key, wages, rent, rate, dump):
    """(largest relative price difference, discrete differences that are not ties, rounds new, rounds old)."""
    (new_prices, new_rounds, _r, new_chosen), (old_prices, old_rounds, _o, old_chosen) = both_solves(
        entries_by_key, wages, rent, rate, dump)
    largest = max(relative_price_change(old_prices[material], new_prices[material]) for material in old_prices
                  if max(abs(old_prices[material]), abs(new_prices[material])) > DUST_HOURS_PER_UNIT)
    untied = []
    for material, recipe in old_chosen.items():
        if new_chosen.get(material) == recipe:
            continue
        other = cheapest_price_of(entries_by_key, wages, rent, rate, dump, old_prices, material, new_chosen.get(material))
        if other is None or relative_price_change(old_prices[material], other) > TIE_TOLERANCE:
            untied.append((material, recipe, new_chosen.get(material)))
    untied += [material for material in set(old_prices) ^ set(new_prices)]
    return largest, untied, new_rounds, old_rounds


class RecordedRomeYear(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        production, _duplicates = engine_seam.load_production()
        with open(FIXTURE) as handle:
            recorded = json.load(handle)
        cls.production = production
        cls.sets = {name: {key: production[key] for key in keys} for name, keys in recorded["entry_sets"].items()}
        cls.cases = recorded["cases"]

    def test_prices_agree_within_the_engine_tolerance_and_no_choice_differs_but_ties(self):
        for case in self.cases:
            largest, untied, new_rounds, old_rounds = compare(
                self.sets[case["entries"]], case["wages"], case["rent"], case["rate"], case["dump"])
            self.assertLess(largest, 10 * ENGINE_TOLERANCE)
            self.assertEqual(untied, [])
            self.assertLess(new_rounds, old_rounds)

    def test_random_variations_of_the_recorded_inputs(self):
        generator = random.Random(968)
        for _ in range(6):
            case = generator.choice(self.cases)
            entries = dict(self.sets[case["entries"]])
            for key in generator.sample(sorted(entries), len(entries) // 10):
                del entries[key]
            wages = {trade: wage * generator.uniform(0.5, 2.0) for trade, wage in case["wages"].items()}
            rent = {material: rent * generator.uniform(0.0, 3.0) for material, rent in case["rent"].items()}
            largest, untied, _new_rounds, _old_rounds = compare(entries, wages, rent, generator.uniform(0.0, 0.2), case["dump"])
            self.assertLess(largest, 10 * ENGINE_TOLERANCE)
            self.assertEqual(untied, [])

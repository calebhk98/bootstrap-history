"""The plan kernel plans every kind of producer as `producers.plan` plans it, to the last bit: a recipe with tool wear and fallbacks, a crew whose
practice stretches the recipe's hours, a recipe with a zero quantity or hour entry. `plan_year.plans_of` (one kernel over the year arrays) is
compared with `producers.plan` on producers written out for each kind and on seeded random ones; no game is run.

Every row is compared, and must equal exactly (`test_year_speed_plans.py` compares the plain recipes on a played game)."""

QUICK_TOPIC = True

import random
import unittest
from dataclasses import replace

from sim import jit
from sim.economy import plan_year, producers
from sim.economy.types import Recipe, ToolFallback
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_costs import refreshed
from sim.economy.market_memory import KEY_SEPARATOR
from sim.tests.year_close_fixture import AREAS, GOODS, MONEY, economy_of

STRETCHED_CREW = {"labourer": 2.0, "smith": 9.0}


def tool_recipe(rng, name):
    """Inputs good0 and good1 (good1 is the tool that wears), outputs good2 (and sometimes good3), two trades; good1 is replaced by good4
    (drawn at 0.5 to 2 units a run, 1.4 times the smith's hours), then by hand (2.5 times)."""
    return Recipe(name, {"good0": rng.uniform(1, 4), "good1": rng.uniform(0.2, 1.0)},
                  {"good2": rng.uniform(1, 3), **({"good3": rng.uniform(0.2, 1.0)} if rng.random() < 0.5 else {})},
                  {"labourer": rng.uniform(0.5, 3), "smith": rng.uniform(0.5, 3)}, tool_wear={"good1": 0.4},
                  tool_fallbacks={"good1": (ToolFallback("good4", rng.uniform(0.5, 2.0), 1.4, ("smith",)),
                                            ToolFallback("", 0.0, 2.5, ("smith", "labourer")))})


def cheap_substitute_recipe(rng, name):
    """A tool whose substitute is nearly free (a few hundredths of a unit of good4 a run, 1.05 times the smith's hours): the substitute caps the
    most the tool is bid, below its price."""
    return Recipe(name, {"good0": rng.uniform(1, 4), "good1": 0.4}, {"good2": rng.uniform(4, 9)},
                  {"labourer": rng.uniform(0.5, 3), "smith": rng.uniform(0.5, 3)}, tool_wear={"good1": 0.4},
                  tool_fallbacks={"good1": (ToolFallback("good4", rng.uniform(0.02, 0.06), 1.05, ("smith", "labourer")),
                                            ToolFallback("", 0.0, 1.2, ("smith",)))})


def zero_entry_recipe(rng, name):
    """A recipe that lists an input, an output and an hours entry at zero."""
    return Recipe(name, {"good0": rng.uniform(1, 4), "good5": 0.0}, {"good2": rng.uniform(1, 3), "good3": 0.0},
                  {"labourer": rng.uniform(0.5, 3), "smith": 0.0})


def wear_without_fallback_recipe(rng, name):
    return Recipe(name, {"good0": rng.uniform(1, 4), "good1": 0.3}, {"good2": rng.uniform(1, 3)}, {"smith": rng.uniform(0.5, 3)},
                  tool_wear={"good1": 0.3})


def economy_with(seed, builders, producer_count=70):
    """The random economy of `seed` with recipe0 to recipe3 replaced by the written-out kinds in `builders`, and a third of the producers
    given a crew whose practice stretches the hours."""
    setup, record, view, _ledger, area_map = economy_of(seed, producer_count=producer_count)
    rng = random.Random(seed)
    for good in GOODS:      # a zero input still has to be priced for the plain plan to price its paying prices
        for area in AREAS:
            record.memory.prices.setdefault(good + KEY_SEPARATOR + area, 2.0)
    for index, build in enumerate(builders):
        setup.recipes["recipe%d" % index] = build(rng, "recipe%d" % index)
    for number, producer_id in enumerate(sorted(record.producers)):
        if number % 3 == 0:
            record.producers[producer_id] = replace(record.producers[producer_id], crew_runs=dict(STRETCHED_CREW))
    arrays = refreshed(YearArrays.build(setup, record, area_map, view), setup, record, view)
    return setup, record, view, arrays


def same(left, right):
    """Equal to the bit; without the compiler (ROME_NO_JIT) numpy's `log` and `erf` may differ from the kernel's in the last digit."""
    if left == right or (left != left and right != right):
        return True
    return not jit.ENABLED and abs(left - right) <= 1e-12 * max(abs(left), abs(right))


class KernelPlansAreThePlainPlans(unittest.TestCase):

    def compare(self, setup, record, view, arrays):
        """(producers compared, producers whose plan runs); every field of every plan must equal the plain plan's."""
        plans = plan_year.plans_of(setup, record, view, arrays, MONEY)
        compared = running = 0
        for producer_id in plans.ids:
            producer = record.producers[producer_id]
            plain = producers.plan(producer, setup.recipes[producer.recipe_id], view, record.book.balance(producer_id, MONEY))
            found = plans.plan_of(producer_id)
            compared += 1
            running += plain.runs > 0.0
            for field in ("runs", "wanted_runs", "wage_line"):
                self.assertTrue(same(getattr(found, field), getattr(plain, field)), (producer_id, field, found, plain))
            self.assertEqual(len(found.bids), len(plain.bids), producer_id)
            self.assertEqual(len(found.labour_bids), len(plain.labour_bids), producer_id)
            for mine, theirs in zip(found.bids, plain.bids):
                for field in ("buyer", "good", "area", "tile", "floor_quantity", "reference_price", "budget", "maximum_price"):
                    self.assertTrue(same(getattr(mine, field), getattr(theirs, field)), (producer_id, mine.good, field, mine, theirs))
            for mine, theirs in zip(found.labour_bids, plain.labour_bids):
                for field in ("employer", "trade", "area", "hours", "maximum_wage"):
                    self.assertTrue(same(getattr(mine, field), getattr(theirs, field)), (producer_id, mine.trade, field, mine, theirs))
        return compared, running

    def test_tool_wear_and_fallbacks(self):
        compared = running = bids = 0
        for seed in range(6):
            found = self.compare(*economy_with(seed, [tool_recipe, tool_recipe, tool_recipe, tool_recipe]))
            compared, running = compared + found[0], running + found[1]
        self.assertGreater(compared, 200)
        self.assertGreater(running, 60)

    def test_substitute_caps_the_bid_for_the_tool(self):
        compared = capped = 0
        for seed in range(6):
            setup, record, view, arrays = economy_with(seed, [cheap_substitute_recipe] * 4)
            found = self.compare(setup, record, view, arrays)
            compared += found[0]
            plans = plan_year.plans_of(setup, record, view, arrays, MONEY)
            capped += sum(bid.maximum_price < bid.reference_price for producer_id in plans.ids for bid in plans.plan_of(producer_id).bids)
        self.assertGreater(compared, 200)
        self.assertGreater(capped, 20)

    def test_stretched_hours_of_plain_recipes(self):
        compared, running = self.compare(*economy_with(3, []))
        self.assertGreater(compared, 15)
        self.assertGreater(running, 5)

    def test_zero_entries(self):
        compared = running = 0
        for seed in range(6):
            found = self.compare(*economy_with(seed, [zero_entry_recipe, zero_entry_recipe, zero_entry_recipe, zero_entry_recipe]))
            compared, running = compared + found[0], running + found[1]
        self.assertGreater(compared, 200)
        self.assertGreater(running, 60)

    def test_tool_wear_without_fallbacks(self):
        compared, running = self.compare(*economy_with(2, [wear_without_fallback_recipe] * 4))
        self.assertGreater(compared, 50)
        self.assertGreater(running, 15)

    def test_mixed_kinds_of_random_economies(self):
        compared = running = 0
        for seed in range(10, 22):
            found = self.compare(*economy_with(seed, [tool_recipe, zero_entry_recipe, wear_without_fallback_recipe, tool_recipe],
                                               producer_count=90))
            compared, running = compared + found[0], running + found[1]
        self.assertGreater(compared, 800)
        self.assertGreater(running, 200)


if __name__ == "__main__":
    unittest.main()

"""kept_carriage_costs searches a source tile's carriage costs once while the techniques held, the ways built and the
towns stay the same, and again when any of them changes."""

QUICK_TOPIC = True

import unittest

from sim.demography.urban import kept_carriage_costs


def counting_search():
    calls = []

    def search(origins, modes, improvements, mode_costs, handling_costs, held, world_map, within):
        calls.append(tuple(origins))
        return {town: float(len(improvements)) + len(held) for town in within}
    return search, calls


class KeptCarriageCostsTest(unittest.TestCase):
    def test_costs_kept_while_inputs_unchanged(self):
        search, calls = counting_search()
        kept = {}
        held = frozenset({"a"})
        first = kept_carriage_costs(kept, ["x", "y"], ["x", "y", "z"], ["road"], held, {"road": {"e1": True}}, search)
        again = kept_carriage_costs(kept, ["y", "x"], ["x", "y", "z"], ["road"], held, {"road": {"e1": True}}, search)
        self.assertEqual(first, again)
        self.assertEqual(calls, [("x",), ("y",)])

    def test_searched_again_when_a_way_is_built_a_technique_held_or_a_new_town_appears(self):
        search, calls = counting_search()
        kept = {}
        kept_carriage_costs(kept, ["x"], ["x", "y"], ["road"], frozenset({"a"}), {"road": {"e1": True}}, search)
        kept_carriage_costs(kept, ["x"], ["x", "y"], ["road"], frozenset({"a"}), {"road": {"e1": True, "e2": True}}, search)
        both = {"road": {"e1": True, "e2": True}}
        kept_carriage_costs(kept, ["x"], ["x", "y"], ["road"], frozenset({"a", "b"}), both, search)
        result = kept_carriage_costs(kept, ["x"], ["x", "y", "z"], ["road"], frozenset({"a", "b"}), both, search)
        fewer = kept_carriage_costs(kept, ["x"], ["x"], ["road"], frozenset({"a", "b"}), both, search)
        self.assertEqual(len(calls), 4)
        self.assertEqual(set(fewer["x"]), {"x", "y", "z"})
        self.assertEqual(set(result["x"]), {"x", "y", "z"})

    def test_a_new_source_is_searched_without_repeating_the_kept_ones(self):
        search, calls = counting_search()
        kept = {}
        kept_carriage_costs(kept, ["x"], ["x", "y"], ["road"], frozenset(), {}, search)
        kept_carriage_costs(kept, ["x", "y"], ["x", "y"], ["road"], frozenset(), {}, search)
        self.assertEqual(calls, [("x",), ("y",)])


if __name__ == "__main__":
    unittest.main()

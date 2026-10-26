"""Assembled views: caching, version channels, derived freshness, seats, keys, quotes and the shadow check."""

QUICK_TOPIC = True

import unittest

from sim.assembly.api import StaleView
from sim.tests.assembly_fixture import build


def count(module, name):
    return module.calls.count(name)


class ViewFreshnessTest(unittest.TestCase):
    def setUp(self):
        self.assembly = build()
        self.base = self.assembly.modules["base"]
        self.views = self.assembly.views
        self.clock = self.assembly.clock

    def test_a_view_read_twice_computes_once(self):
        self.assertEqual(self.views["double"](), 2)
        self.assertEqual(self.views["double"](), 2)
        self.assertEqual(count(self.base, "double"), 1)

    def test_a_bump_recomputes(self):
        self.views["double"]()
        self.base.value = 5
        self.base.bump("data")
        self.assertEqual(self.views["double"](), 10)
        self.assertEqual(count(self.base, "double"), 2)

    def test_a_bump_of_another_channel_does_not_recompute(self):
        self.views["double"]()
        self.base.bump("other")
        self.views["double"]()
        self.assertEqual(count(self.base, "double"), 1)

    def test_a_derived_view_recomputes_when_an_input_channel_moves(self):
        top = self.assembly.modules["top"]
        self.assertEqual(self.views["derived"](), 3)
        self.base.value = 4
        self.base.bump("data")
        self.assertEqual(self.views["derived"](), 9)
        self.assertEqual(count(top, "derived"), 2)

    def test_a_derived_view_does_not_recompute_when_nothing_moved(self):
        top = self.assembly.modules["top"]
        self.views["derived"]()
        self.base.bump("other")
        self.views["derived"]()
        self.assertEqual(count(top, "derived"), 1)

    def test_seat_scoped_view_keeps_one_entry_per_seat(self):
        self.base.per_seat = {"a": 5, "b": 7}
        self.clock.act_as("a")
        self.assertEqual(self.views["mine"](), 5)
        self.clock.act_as("b")
        self.assertEqual(self.views["mine"](), 7)
        self.clock.act_as("a")
        self.assertEqual(self.views["mine"](), 5)
        self.assertEqual(count(self.base, "mine"), 2)
        self.assertEqual(set(self.views["mine"].entries), {"a", "b"})

    def test_a_seat_bump_recomputes_only_that_seat(self):
        self.base.per_seat = {"a": 5, "b": 7}
        self.clock.act_as("a")
        self.views["mine"]()
        self.clock.act_as("b")
        self.views["mine"]()
        self.base.per_seat["a"] = 6
        self.base.bump_seat("mine", "a")
        self.assertEqual(self.views["mine"](), 7)
        self.assertEqual(count(self.base, "mine"), 2)
        self.clock.act_as("a")
        self.assertEqual(self.views["mine"](), 6)
        self.assertEqual(count(self.base, "mine"), 3)

    def test_acting_as_the_same_seat_again_does_not_recompute(self):
        self.clock.act_as("a")
        self.views["mine"]()
        self.clock.act_as("a")
        self.views["mine"]()
        self.assertEqual(count(self.base, "mine"), 1)

    def test_keyed_view_computes_per_key_once(self):
        self.assertEqual(self.views["keyed"][3], 3)
        self.assertEqual(self.views["keyed"][3], 3)
        self.assertEqual(self.views["keyed"][4], 4)
        self.assertEqual(self.base.calls.count(("keyed", 3)), 1)
        self.assertEqual(self.base.calls.count(("keyed", 4)), 1)

    def test_a_bump_drops_every_key(self):
        self.views["keyed"][3]
        self.views["keyed"][4]
        self.base.value = 2
        self.base.bump("data")
        self.assertEqual(self.views["keyed"][3], 6)
        self.assertEqual(self.views["keyed"][4], 8)
        self.assertEqual(self.base.calls.count(("keyed", 3)), 2)
        self.assertEqual(self.base.calls.count(("keyed", 4)), 2)

    def test_a_keyed_view_called_without_a_key_is_a_type_error(self):
        with self.assertRaises(TypeError):
            self.views["keyed"]()

    def test_a_table_indexed_is_a_type_error(self):
        with self.assertRaises(TypeError):
            self.views["double"][1]

    def test_a_quote_always_computes(self):
        self.assertEqual(self.views["quote"](10), 11)
        self.assertEqual(self.views["quote"](10), 11)
        self.assertEqual(count(self.base, "quote"), 2)

    def test_an_uncached_view_always_computes(self):
        self.views["uncached"]()
        self.views["uncached"]()
        self.assertEqual(count(self.base, "uncached"), 2)

    def test_bump_everything_invalidates_all(self):
        self.views["double"]()
        self.views["keyed"][2]
        self.views["derived"]()
        self.clock.bump_everything()
        self.views["double"]()
        self.views["keyed"][2]
        self.views["derived"]()
        self.assertEqual(count(self.base, "double"), 2)
        self.assertEqual(self.base.calls.count(("keyed", 2)), 2)
        self.assertEqual(count(self.assembly.modules["top"], "derived"), 2)

    def test_a_table_with_arguments_is_a_type_error(self):
        with self.assertRaises(TypeError):
            self.views["double"](1)


class ShadowCheckTest(unittest.TestCase):
    def test_silent_mutation_raises_stale_view(self):
        assembly = build(shadow_every=1)
        assembly.views["double"]()
        assembly.modules["base"].value = 9
        with self.assertRaises(StaleView):
            assembly.views["double"]()

    def test_silent_mutation_on_a_keyed_view_raises_stale_view(self):
        assembly = build(shadow_every=1)
        assembly.views["keyed"][2]
        assembly.modules["base"].value = 9
        with self.assertRaises(StaleView):
            assembly.views["keyed"][2]

    def test_shadow_off_serves_the_cached_value(self):
        assembly = build(shadow_every=0)
        assembly.views["double"]()
        assembly.modules["base"].value = 9
        self.assertEqual(assembly.views["double"](), 2)

    def test_honest_bumps_never_raise(self):
        assembly = build(shadow_every=1)
        base = assembly.modules["base"]
        for value in (3, 4, 5):
            base.value = value
            base.bump("data")
            self.assertEqual(assembly.views["double"](), value * 2)
            self.assertEqual(assembly.views["double"](), value * 2)

    def test_shadow_every_n_checks_on_the_nth_cached_read(self):
        assembly = build(shadow_every=3)
        assembly.views["double"]()
        assembly.modules["base"].value = 9
        assembly.views["double"]()
        assembly.views["double"]()
        with self.assertRaises(StaleView):
            assembly.views["double"]()


if __name__ == "__main__":
    unittest.main()

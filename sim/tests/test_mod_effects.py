"""Complaint 496: the rules of a mod effect operation that hold before it touches the world: a mod's kinds and edges are
forced into its namespace, every change needs a cause, an amount is a number of zero or more, a death share is a share, and a
store is written only by the mod that declared it. Called with no game, or a host that holds only its stores. What the
operations hand to the normal rules is in `test_mod_effect_operations`."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents.api import edges
from sim.engine import mod_stores
from sim.engine.mod_effects import ModEffects
from sim.engine.mod_stores import ModStoresMixin
from sim.engine.mods import ModError
from sim.tests.bridge_send import attach_send

ACME, BETA = "test_acme_k3f9", "test_beta_k3f9"


class Host(ModStoresMixin):
    """A game with nothing but its saved stores."""

    def __init__(self):
        self.state = SimpleNamespace(stores={})
        attach_send(self)


class Names(unittest.TestCase):

    def test_a_mods_kind_is_forced_into_its_namespace_and_not_doubled(self):
        self.assertEqual(ModEffects(ACME).kind("deaths"), ACME + ":deaths")
        self.assertEqual(ModEffects(ACME).kind(ACME + ":deaths"), ACME + ":deaths")

    def test_the_base_game_keeps_its_kinds_bare(self):
        self.assertEqual(ModEffects().kind("flood"), "flood")

    def test_a_declared_edge_and_the_mods_own_edge_are_accepted(self):
        effects = ModEffects(ACME)
        self.assertEqual(effects.edge_name(edges.EDGE_OFFICIALS), edges.EDGE_OFFICIALS)
        self.assertEqual(effects.edge_name("edge:%s:tithe" % ACME), "edge:%s:tithe" % ACME)

    def test_an_undeclared_edge_or_another_mods_edge_is_refused(self):
        effects = ModEffects(ACME)
        for edge in ("nowhere", "edge:%s:tithe" % BETA, None):
            with self.assertRaises(ModError, msg=edge):
                effects.edge_name(edge)


class Arguments(unittest.TestCase):

    def test_a_change_needs_a_cause_in_words(self):
        effects = ModEffects(ACME)
        for cause in ("", "  ", None, 3):
            with self.assertRaises(ModError, msg=cause):
                effects.need_cause(cause)
        self.assertEqual(effects.need_cause("a curse"), "a curse")

    def test_an_amount_is_a_number_of_zero_or_more(self):
        effects = ModEffects(ACME)
        for amount in (-1.0, True, "5", float("nan"), None):
            with self.assertRaises(ModError, msg=amount):
                effects.add_goods(None, "account", "grain", "tile", amount, "a gift")
        with self.assertRaises(ModError):
            effects.add_goods(None, "account", "grain", "tile", 1.0, "a gift", edge="somewhere")

    def test_a_death_share_is_between_zero_and_one_and_needs_a_cause(self):
        effects = ModEffects(ACME)
        for share in (-0.1, 1.5):
            with self.assertRaises(ModError, msg=share):
                effects.kill_people(None, "country", share, "too many")
        with self.assertRaises(ModError):
            effects.kill_people(None, "country", 0.1, "")


class StoreWrites(unittest.TestCase):

    def setUp(self):
        mod_stores.forget_mod_stores()
        mod_stores.declare(mod_stores.StoreSpec(ACME + ":mana", ACME, "tile", 0.0, "mana"), "test")
        self.host = Host()

    def tearDown(self):
        mod_stores.forget_mod_stores()

    def test_a_store_write_is_the_declaring_mods_only(self):
        ModEffects(ACME).write_store(self.host, ACME + ":mana", "tile_1", 3.0)
        self.assertEqual(self.host.stores.view(ACME + ":mana").get("tile_1"), 3.0)
        with self.assertRaises(ModError):
            ModEffects(BETA).write_store(self.host, ACME + ":mana", "tile_1", 1.0)
        self.assertEqual(self.host.stores.view(ACME + ":mana").get("tile_1"), 3.0)


if __name__ == "__main__":
    unittest.main()

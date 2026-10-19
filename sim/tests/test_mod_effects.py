"""Complaint 496: mod code changes the world through effect operations that follow the normal rules.

Slow topic: it builds a two-country game (not in the quick tier)."""
import random
import unittest
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.agents.api import edges, seed_strata
from sim.engine import mod_code, mod_stores, world_events, world_hazards
from sim.engine.agents_port import SimWorld
from sim.engine.agents_port_cast import seed_opening_cast
from sim.engine.mod_effects import ModEffects, people_of
from sim.engine.mods import ModError
from sim.tests import economy_fixture

PARTNER = "han_china_100ad"
ACME, BETA = "test_acme_k3f9", "test_beta_k3f9"


def two_country_game():
    civ = S.load_civ("rome_100ad")
    game = build_unopened(lambda: S.Sim(NODES, list(ORDER), random.Random(1), events=True, manual=True, civ=civ))
    game.partner_countries = lambda: [PARTNER]
    game.partners_in_agent_economy = lambda: [PARTNER]
    game.goal, game.done_year = GOAL, {}
    seed_opening_cast(game)
    seed_strata(game.actors, SimWorld(game))
    return game


class StubPort:
    """Stands in for `sim.economy`: hands out a small hand-built economy."""

    def __init__(self, economy):
        self.agent = self
        self._economy = economy

    def economy(self):
        return self._economy


class EffectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mod_stores.forget_mod_stores()
        mod_stores.declare(mod_stores.StoreSpec(ACME + ":mana", ACME, "tile", 0.0, "mana"), "test")
        cls.api = mod_code.ModCodeApi(ACME)

    @classmethod
    def tearDownClass(cls):
        mod_stores.forget_mod_stores()

    def setUp(self):
        self.game = two_country_game()
        self.effects = self.api.effects

    def test_money_through_a_named_edge_keeps_the_books(self):
        government = self.game.actors.get("government:rome_100ad")
        held = government.money
        self.effects.pay_edge(self.game, government.actor_id, edges.EDGE_OFFICIALS, 10.0, "a bribe")
        self.assertAlmostEqual(government.money, held - 10.0)
        self.assertAlmostEqual(self.game.edge(edges.EDGE_OFFICIALS).volume(), 10.0)
        self.effects.receive_from_edge(self.game, government.actor_id, edges.EDGE_OFFICIALS, 10.0, "returned")
        self.assertAlmostEqual(government.money, held)
        self.assertTrue(self.game.state.actors.purses.book.check_conservation(1e-9).ok)

    def test_a_money_move_without_a_named_edge_is_refused(self):
        government = self.game.actors.get("government:rome_100ad")
        for edge in (None, "", "nowhere", "edge:%s:x" % BETA):
            with self.assertRaises(ModError, msg=edge):
                self.effects.pay_edge(self.game, government.actor_id, edge, 1.0, "x")
        with self.assertRaises(ModError):
            self.effects.pay_edge(self.game, government.actor_id, edges.EDGE_OFFICIALS, -1.0, "x")
        self.effects.pay_edge(self.game, government.actor_id, "edge:%s:tithe" % ACME, 1.0, "own edge")

    def test_goods_added_and_removed_appear_in_the_book(self):
        economy, _ = economy_fixture.run(years=1)
        self.game.__dict__["_economy_port"] = StubPort(economy)
        book, tile, grain = economy.record.book, economy_fixture.TOWN, economy_fixture.GRAIN
        net_before = book.edge_goods_net("edge:production", grain)
        consumed_before = book.edge_goods_net("edge:consumption", grain)
        self.effects.add_goods(self.game, "mod_account", grain, tile, 5.0, "a gift of grain")
        self.assertAlmostEqual(book.stock("mod_account", grain, tile), 5.0)
        self.effects.remove_goods(self.game, "mod_account", grain, tile, 2.0, "a fire")
        self.assertAlmostEqual(book.stock("mod_account", grain, tile), 3.0)
        self.assertAlmostEqual(abs(book.edge_goods_net("edge:production", grain) - net_before), 5.0)
        self.assertAlmostEqual(abs(book.edge_goods_net("edge:consumption", grain) - consumed_before), 2.0)
        self.assertTrue(book.check_conservation(1e-9).ok)
        with self.assertRaises(Exception):
            self.effects.remove_goods(self.game, "mod_account", grain, tile, 99.0, "too much")
        with self.assertRaises(ModError):
            self.effects.add_goods(self.game, "mod_account", grain, tile, 1.0, "x", edge="somewhere")

    def test_killing_people_cuts_the_country_and_writes_an_event(self):
        before = people_of(self.game, PARTNER)
        entry = self.effects.kill_people(self.game, PARTNER, 0.25, "a curse")
        self.assertAlmostEqual(people_of(self.game, PARTNER), before * 0.75)
        self.assertEqual(entry["kind"], ACME + ":deaths")
        self.assertAlmostEqual(entry["facts"]["died"], before * 0.25)
        home = people_of(self.game, "rome_100ad")
        self.effects.kill_people(self.game, "rome_100ad", 0.1, "a curse")
        self.assertAlmostEqual(people_of(self.game, "rome_100ad"), home * 0.9, delta=home * 1e-6)
        with self.assertRaises(ModError):
            self.effects.kill_people(self.game, PARTNER, 0.1, "")
        with self.assertRaises(ModError):
            self.effects.kill_people(self.game, PARTNER, 1.5, "too many")

    def test_moving_people_between_strata_keeps_the_total(self):
        strata = [actor.actor_id for actor in self.game.actors.of_kind("stratum")
                  if (actor.record.country or "rome_100ad") == PARTNER]
        first, second = strata[0], strata[1]
        before = people_of(self.game, PARTNER)
        members = self.game.actors.get(first).record.members
        entry = self.effects.move_people(self.game, first, second, members / 2, "migration")
        self.assertAlmostEqual(entry["facts"]["moved"], members / 2)
        self.assertAlmostEqual(people_of(self.game, PARTNER), before)
        with self.assertRaises(ModError):
            self.effects.move_people(self.game, first, "government:rome_100ad", 1.0, "not a stratum")

    def test_a_tile_transfer_writes_a_world_event_with_its_cause(self):
        tile = self.game.tiles_owned_by("rome_100ad")[0]
        self.effects.transfer_tile(self.game, tile, PARTNER, "a treaty")
        self.assertEqual(self.game.tile_owner(tile), PARTNER)
        self.assertEqual([row["cause"] for row in world_events.rows(self.game, "tile_transfer")], ["a treaty"])
        with self.assertRaises(ModError):
            self.effects.transfer_tile(self.game, tile, "rome_100ad", " ")

    def test_a_store_write_is_the_declaring_mods_only(self):
        tile = sorted(self.game.tile_owner_map())[0]
        self.effects.write_store(self.game, ACME + ":mana", tile, 3.0)
        self.assertEqual(self.game.stores.view(ACME + ":mana").get(tile), 3.0)
        with self.assertRaises(ModError):
            ModEffects(BETA).write_store(self.game, ACME + ":mana", tile, 1.0)

    def test_a_recorded_event_carries_the_mods_namespace_and_a_cause(self):
        entry = self.effects.record_event(self.game, "omen", "a comet", actors=["rome_100ad"], brightness=2)
        self.assertEqual((entry["kind"], entry["cause"], entry["facts"]), (ACME + ":omen", "a comet", {"brightness": 2}))
        with self.assertRaises(ModError):
            self.effects.record_event(self.game, "omen", "")

    def test_the_base_game_hazards_use_the_same_operation(self):
        owners = []
        real = ModEffects.kill_people

        def spy(effects, *args, **kwargs):
            owners.append(effects.owner)
            return real(effects, *args, **kwargs)
        with mock.patch.object(ModEffects, "kill_people", spy):
            world_hazards.hit(self.game, PARTNER, {"kind": "flood", "cause": "a flood", "population_loss": 0.1})
        self.assertEqual(owners, [""])
        self.assertEqual(world_events.rows(self.game, "flood")[0]["kind"], "flood")


if __name__ == "__main__":
    unittest.main()

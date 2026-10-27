"""`ModEffects`, called on inputs built here with no game: `move_people` moves people between two strata with the
total unchanged, capped by who is there; `edge_name` accepts only declared edges or the mod's own; `record_event` forces
the mod's namespace and a cause. The stand-in game answers `actors`, `civ` and the event log only."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents.api import Stratum, stratum_id
from sim.agents.records import ActorRecord
from sim.engine.mod_effects import ModEffects, people_of
from sim.agents.api import edges
from sim.engine.mods import ModError
from sim.tests.bridge_send import attach_send
from sim.tests.ui_stand_in import Game

HOME, ABROAD = "home_land", "far_land"


class StandInActors:
    def __init__(self, actors):
        self.by_id = {actor.actor_id: actor for actor in actors}

    def get(self, actor_id):
        return self.by_id.get(actor_id)

    def of_kind(self, kind):
        return [actor for actor in self.by_id.values() if actor.record.kind == kind]


def stratum(country, name, members):
    record = ActorRecord(kind="stratum", stratum=name, members=members, country=country)
    return Stratum(stratum_id(country, name), record)


def stand_in_game():
    farmers, artisans, foreign = stratum(None, "farmers", 1000.0), stratum(None, "artisans", 200.0), stratum(ABROAD, "farmers", 50.0)
    government = SimpleNamespace(actor_id="government:home", record=ActorRecord(kind="government"))
    game = Game(actors=StandInActors([farmers, artisans, foreign, government]), civ={"id": HOME},
                           state=SimpleNamespace(scenario=SimpleNamespace(year=100)),
                           population=SimpleNamespace(total=1200.0))
    attach_send(game)
    return game, farmers, artisans, foreign


class MovePeopleTests(unittest.TestCase):
    def setUp(self):
        self.effects = ModEffects("test_mod")
        self.game, self.farmers, self.artisans, self.foreign = stand_in_game()

    def test_the_count_leaves_one_stratum_and_joins_the_other(self):
        entry = self.effects.move_people(self.game, self.farmers.actor_id, self.artisans.actor_id, 300.0, "a reform")
        self.assertEqual((self.farmers.record.members, self.artisans.record.members), (700.0, 500.0))
        self.assertEqual(entry["facts"]["moved"], 300.0)
        self.assertEqual(entry["cause"], "a reform")

    def test_the_total_of_the_country_is_unchanged(self):
        before = sum(actor.record.members for actor in self.game.actors.of_kind("stratum"))
        self.effects.move_people(self.game, self.farmers.actor_id, self.artisans.actor_id, 123.0, "a reform")
        self.assertAlmostEqual(sum(actor.record.members for actor in self.game.actors.of_kind("stratum")), before)

    def test_a_move_abroad_changes_each_countrys_people_by_the_count(self):
        self.effects.move_people(self.game, self.farmers.actor_id, self.foreign.actor_id, 10.0, "migration")
        self.assertEqual(people_of(self.game, ABROAD), 60.0)
        self.assertEqual(self.farmers.record.members, 990.0)

    def test_no_more_move_than_the_source_holds(self):
        entry = self.effects.move_people(self.game, self.artisans.actor_id, self.farmers.actor_id, 1.0e6, "exodus")
        self.assertEqual(entry["facts"]["moved"], 200.0)
        self.assertEqual(self.artisans.record.members, 0.0)

    def test_only_strata_can_be_named_and_a_cause_is_needed(self):
        with self.assertRaises(ModError):
            self.effects.move_people(self.game, self.farmers.actor_id, "government:home", 1.0, "not a stratum")
        with self.assertRaises(ModError):
            self.effects.move_people(self.game, self.farmers.actor_id, "nobody", 1.0, "no such actor")
        with self.assertRaises(ModError):
            self.effects.move_people(self.game, self.farmers.actor_id, self.artisans.actor_id, 1.0, "")
        with self.assertRaises(ModError):
            self.effects.move_people(self.game, self.farmers.actor_id, self.artisans.actor_id, -1.0, "negative")
        self.assertEqual(self.farmers.record.members, 1000.0)


class NamesAndEventsTests(unittest.TestCase):
    def test_a_declared_edge_and_the_mods_own_edge_are_named_edges(self):
        effects = ModEffects("test_mod")
        self.assertEqual(effects.edge_name(edges.EDGE_OFFICIALS), edges.EDGE_OFFICIALS)
        self.assertEqual(effects.edge_name("edge:test_mod:tithe"), "edge:test_mod:tithe")

    def test_anything_else_is_not_a_named_edge(self):
        effects = ModEffects("test_mod")
        for edge in (None, "", "nowhere", "edge:other_mod:x"):
            with self.assertRaises(ModError, msg=edge):
                effects.edge_name(edge)

    def test_the_base_game_has_no_namespace_of_its_own_to_borrow(self):
        with self.assertRaises(ModError):
            ModEffects("").edge_name("edge:test_mod:tithe")

    def test_a_recorded_event_carries_the_mods_namespace_and_a_cause(self):
        game, *_ = stand_in_game()
        entry = ModEffects("test_mod").record_event(game, "omen", "a comet", actors=[HOME], brightness=2)
        self.assertEqual((entry["kind"], entry["cause"], entry["facts"]), ("test_mod:omen", "a comet", {"brightness": 2}))
        self.assertEqual(game.world_event_log.world_events("test_mod:omen"), [entry])

    def test_an_event_without_a_cause_is_refused_and_not_recorded(self):
        game, *_ = stand_in_game()
        with self.assertRaises(ModError):
            ModEffects("test_mod").record_event(game, "omen", "")
        self.assertEqual(game.world_event_log.world.world_events, [])


if __name__ == "__main__":
    unittest.main()

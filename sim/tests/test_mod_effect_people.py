"""`ModEffects`, called on inputs built here with no game: `move_people` moves people between two strata with the
total unchanged, capped by who is there; `edge_name` accepts only declared edges or the mod's own; `record_event` forces
the mod's namespace and a cause. The stand-in game answers `actors`, `civ` and the event log only."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors.api import MoveStratumPeople
from sim.actors.contact import Contact
from sim.agents.api import Stratum, stratum_id
from sim.agents.records import ActorRecord
from sim.engine.mod_effects import ModEffects, people_of
from sim.agents.api import edges
from sim.content.api import ModError
from sim.refusal import Refusal, cause_of
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


class MovePeopleEffectTests(unittest.TestCase):
    def setUp(self):
        self.effects = ModEffects("test_mod")
        self.game, *_ = stand_in_game()
        self.sent = []
        self.answer = {"moved": 300.0, "countries": [HOME, ABROAD]}
        self.game.send = lambda command: self.sent.append(command) or (
            self.answer if isinstance(command, MoveStratumPeople) else {"kind": command.kind, "facts": command.facts, "cause": command.cause,
                                                                         "actors": command.actors})

    def test_the_actors_owner_is_sent_the_move_and_the_event_states_what_moved(self):
        entry = self.effects.move_people(self.game, "stratum:a", "stratum:b", 300.0, "a reform")
        self.assertEqual(self.sent[0], MoveStratumPeople("stratum:a", "stratum:b", 300.0))
        self.assertEqual((entry["kind"], entry["cause"], entry["actors"]), ("test_mod:people_moved", "a reform", (ABROAD, HOME)))
        self.assertEqual(entry["facts"], {"moved": 300.0, "from_stratum": "stratum:a", "to_stratum": "stratum:b"})

    def test_a_refusal_of_the_owner_is_a_mod_error_and_no_event_is_written(self):
        self.answer = Refusal("no_such_stratum", "the cast holds no stratum stratum:b")
        with self.assertRaises(ModError):
            self.effects.move_people(self.game, "stratum:a", "stratum:b", 1.0, "no such stratum")
        self.assertEqual(len(self.sent), 1)

    def test_a_missing_cause_or_a_negative_count_is_refused_before_the_owner_is_sent_anything(self):
        for count, cause in ((1.0, ""), (-1.0, "negative")):
            with self.assertRaises(ModError, msg=cause):
                self.effects.move_people(self.game, "stratum:a", "stratum:b", count, cause)
        self.assertEqual(self.sent, [])


class MoveStratumPeopleTests(unittest.TestCase):
    """The actors module's handler of the command."""

    def setUp(self):
        self.farmers, self.artisans, self.foreign = stratum(None, "farmers", 1000.0), stratum(None, "artisans", 200.0), stratum(ABROAD, "farmers", 50.0)
        actors = {actor.actor_id: actor for actor in (self.farmers, self.artisans, self.foreign)}
        actors["government:home"] = SimpleNamespace(actor_id="government:home", record=ActorRecord(kind="government"))
        self.module = SimpleNamespace(cast=lambda: SimpleNamespace(actors=actors), needs=SimpleNamespace(civilisation=lambda: {"id": HOME}))

    def move(self, source, target, count):
        return Contact.move_stratum_people(self.module, MoveStratumPeople(source.actor_id, target.actor_id, count))

    def test_the_count_leaves_one_stratum_and_joins_the_other(self):
        answer = self.move(self.farmers, self.artisans, 300.0)
        self.assertEqual((self.farmers.record.members, self.artisans.record.members), (700.0, 500.0))
        self.assertEqual(answer, {"moved": 300.0, "countries": [HOME, HOME]})

    def test_a_move_abroad_names_both_countries_and_keeps_the_total(self):
        answer = self.move(self.farmers, self.foreign, 10.0)
        self.assertEqual((self.farmers.record.members, self.foreign.record.members), (990.0, 60.0))
        self.assertEqual(answer["countries"], [HOME, ABROAD])

    def test_no_more_moves_than_the_source_holds(self):
        answer = self.move(self.artisans, self.farmers, 1.0e6)
        self.assertEqual((answer["moved"], self.artisans.record.members), (200.0, 0.0))

    def test_only_strata_can_be_named(self):
        government = SimpleNamespace(actor_id="government:home")
        for target in (government, SimpleNamespace(actor_id="nobody")):
            answer = self.move(self.farmers, target, 1.0)
            self.assertEqual(cause_of(answer), "no_such_stratum")
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

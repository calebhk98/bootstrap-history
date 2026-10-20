"""The country's reading shares are calculated from living people, including migrants."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import (ActorRecord, ActorRegistry, ActorsState, CastEntry,
                            CountryLiteracy, CountryProfile, CountryWorld, seed_cast)
from sim.agents.stratum_year import settle_moves
from sim.engine.state import deserialize_state, serialize_state
from sim.tests.agents_fake_world import FakeWorld


def people(registry, country, name, members, literacy, **plan):
    return registry.add("stratum:%s:%s" % (country or "home", name), ActorRecord(
        kind="stratum", country=country, stratum=name, members=members, literacy=literacy, plan=plan))


class CountryLiteracyTotalsTests(unittest.TestCase):
    def test_weighted_population_and_propertied_population(self):
        registry = ActorRegistry(ActorsState(home_country="home"))
        people(registry, None, "workers", 90, 0.1)
        people(registry, None, "owners", 10, 0.9, property_share=0.3)
        retired = people(registry, None, "departed", 1000, 1.0)
        retired.record.exited_year = 100
        literacy = CountryLiteracy(registry.of_kind("stratum"))
        self.assertAlmostEqual(literacy.get("literacy_general"), 0.18)
        self.assertAlmostEqual(literacy.get("literacy_elite"), 0.9)
        self.assertAlmostEqual(literacy.ceiling(common=0.6, propertied=0.9), 0.63)
        self.assertEqual(CountryLiteracy([]).get("literacy_general"), 0.0)

    def test_teaching_changes_the_records_and_respects_the_ceiling(self):
        registry = ActorRegistry(ActorsState(home_country="home"))
        worker = people(registry, None, "workers", 90, 0.1)
        owner = people(registry, None, "owners", 10, 0.9, property_share=0.3)
        literacy = CountryLiteracy(registry.of_kind("stratum"))
        literacy.set("literacy_general", 0.5, ceiling=0.6)
        self.assertAlmostEqual(literacy.get("literacy_general"), 0.5)
        self.assertGreater(worker.record.literacy, 0.1)
        self.assertEqual(owner.record.literacy, 0.9)
        literacy.set("literacy_general", 1.0, ceiling=0.6)
        self.assertAlmostEqual(literacy.get("literacy_general"), 0.6)
        self.assertLessEqual(worker.record.literacy, 0.6)
        self.assertEqual(owner.record.literacy, 0.9)

    def test_preview_cannot_change_people(self):
        registry = ActorRegistry(ActorsState(home_country="home"))
        worker = people(registry, None, "workers", 100, 0.2)
        literacy = CountryLiteracy(registry.of_kind("stratum"))
        preview = literacy.copy()
        preview.set("literacy_general", 0.7)
        self.assertAlmostEqual(preview.get("literacy_general"), 0.7)
        self.assertEqual(worker.record.literacy, 0.2)

    def test_a_school_teaches_only_the_population_it_reaches(self):
        registry = ActorRegistry(ActorsState(home_country="home"))
        worker = people(registry, None, "workers", 90, 0.1)
        owner = people(registry, None, "owners", 10, 0.5, property_share=0.3)
        literacy = CountryLiteracy(registry.of_kind("stratum"))
        literacy.teach("literacy_general", 0.2, ceiling=0.6)
        self.assertAlmostEqual(literacy.get("literacy_general"), 0.2)
        self.assertEqual(owner.record.literacy, 0.5)
        workers_before = worker.record.literacy
        literacy.teach("literacy_elite", 0.7, ceiling=0.9)
        self.assertAlmostEqual(owner.record.literacy, 0.7)
        self.assertEqual(worker.record.literacy, workers_before)

    def test_country_view_does_not_read_the_home_population(self):
        state = ActorsState(home_country="home")
        registry = ActorRegistry(state)
        people(registry, None, "workers", 1000, 0.9)
        foreign = people(registry, "other", "workers", 100, 0.2)
        view = CountryWorld(FakeWorld(), CountryProfile(country="other"), registry)
        self.assertAlmostEqual(view.literacy("literacy_general"), 0.2)
        foreign.record.literacy = 0.6
        self.assertAlmostEqual(view.literacy("literacy_general"), 0.6)

    def test_migration_keeps_the_number_of_readers(self):
        registry = ActorRegistry(ActorsState(home_country="home"))
        source = people(registry, None, "workers", 90, 0.1)
        target = people(registry, None, "owners", 10, 0.9, property_share=0.3)
        before = CountryLiteracy(registry.of_kind("stratum")).get("literacy_general")
        source.record.moving = {target.actor_id: 20}
        settle_moves(registry)
        literacy = CountryLiteracy(registry.of_kind("stratum"))
        self.assertAlmostEqual(literacy.get("literacy_general"), before)
        self.assertAlmostEqual(literacy.get("literacy_elite"), 11 / 30)

    def test_save_round_trip_keeps_the_same_readers(self):
        state = ActorsState(home_country="home")
        registry = ActorRegistry(state)
        people(registry, None, "workers", 90, 0.1)
        people(registry, None, "owners", 10, 0.9, property_share=0.3)
        before = CountryLiteracy(registry.of_kind("stratum"))
        restored = ActorRegistry(deserialize_state(serialize_state(state), ActorsState))
        after = CountryLiteracy(restored.of_kind("stratum"))
        for field in ("literacy_general", "literacy_elite"):
            self.assertEqual(before.get(field), after.get(field))

    def test_cast_numbers_have_the_same_types_before_and_after_loading(self):
        state = ActorsState()
        registry = ActorRegistry(state)
        seed_cast(registry, "home", [CastEntry(
            actor_id="government:home", kind="government", params={"army": 12})],
            {"home": CountryProfile(country="home")})
        restored = deserialize_state(serialize_state(state), ActorsState)
        self.assertEqual(state.records["government:home"].army, 12)
        self.assertIsInstance(state.records["government:home"].army, float)
        self.assertIsInstance(restored.records["government:home"].army, float)

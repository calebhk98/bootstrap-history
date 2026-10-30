"""Complaint 371, the rule: between years the staff count a registry reports is what its actors employ now. Entry and
group formation change staff after the last actor has acted, and a count kept from before those changes would make an
unbroken game read a different pool from the one a reloaded game reads. The registry is built here with idle firms and a
spawner that changes staff; no game is built."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import Business
from sim.agents.registry import ActorRegistry
from sim.engine.state import ActorRecord, ActorsState

TRADES = ("smith", "scribe")


class IdleWorld:
    year = 100

    def demonstrated(self):
        return set()

    def sectors(self):
        return {}

    def concerns_making(self, material):
        return frozenset()

    def market_forget(self, actor_id):
        pass

    def baseline_knowledge(self):
        return set()

    def materials_made_by(self, node_id):
        return ()

    def market_sale(self, actor_id, material, tonnes, from_concerns=None):
        pass


def registry_of_firms(count):
    state = ActorsState()
    for number in range(count):
        state.records["firm:%03d" % number] = ActorRecord(
            kind="firm", business=Business.running(["plain_%03d" % number]), workforce={"smith": 1.5})
    registry = ActorRegistry(state)
    registry.consider_entry = lambda world: []
    for actor in registry.actors.values():
        actor.advance = lambda world: None
    return registry


def fresh_sum(registry, trade):
    total = 0.0
    for actor_id in sorted(registry.actors):
        total += registry.actors[actor_id].record.workforce.get(trade, 0.0)
    return total


class StaffBetweenYears(unittest.TestCase):
    def advance_with(self, registry, spawner, read_during_last_turn=True):
        registry.extensions.spawners[:] = [("test_spawner", spawner)]
        if read_during_last_turn:
            registry.actors["firm:004"].advance = lambda world: registry.staff_fte("smith")
        registry.advance(IdleWorld())

    def assert_counts_match(self, registry):
        for trade in TRADES:
            self.assertEqual(fresh_sum(registry, trade), registry.staff_fte(trade), trade)

    def test_a_firm_entering_after_the_last_turn_is_counted(self):
        registry = registry_of_firms(5)

        def enter(reg, world):
            reg.add("firm:900", ActorRecord(kind="firm", workforce={"smith": 4.0, "scribe": 0.5}))
            return ["firm:900"]
        self.advance_with(registry, enter)
        self.assertEqual(5 * 1.5 + 4.0, registry.staff_fte("smith"))
        self.assert_counts_match(registry)

    def test_an_actor_taking_on_people_after_the_last_turn_is_counted(self):
        registry = registry_of_firms(5)

        def form_group(reg, world):
            reg.actors["firm:001"].workforce["scribe"] = 2.0
            reg.actors["firm:001"].workforce["smith"] += 1.0
            return []
        self.advance_with(registry, form_group)
        self.assertEqual(5 * 1.5 + 1.0, registry.staff_fte("smith"))
        self.assertEqual(2.0, registry.staff_fte("scribe"))
        self.assert_counts_match(registry)

    def test_the_count_is_right_when_no_turn_read_it(self):
        registry = registry_of_firms(5)

        def enter(reg, world):
            reg.add("firm:901", ActorRecord(kind="firm", workforce={"smith": 3.0}))
            return ["firm:901"]
        self.advance_with(registry, enter, read_during_last_turn=False)
        self.assert_counts_match(registry)


if __name__ == "__main__":
    unittest.main()

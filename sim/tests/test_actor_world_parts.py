"""An `ActorWorld` builds a part when it is first asked for; two worlds never share a part, so each keeps its own turn's memo."""

QUICK_TOPIC = True

import unittest

from sim.actors.world import ActorWorld


class ActorWorldPartsTests(unittest.TestCase):
    def test_a_world_holds_no_part_until_one_is_asked_for(self):
        world = ActorWorld(needs=object())
        self.assertEqual(set(vars(world)) & set(ActorWorld.PARTS), set())

    def test_a_part_is_built_once_and_is_the_same_object_afterwards(self):
        world = ActorWorld(needs=object())
        first = world.revenue
        self.assertIs(world.revenue, first)
        self.assertIs(first.world, world)

    def test_two_worlds_keep_their_own_memo_of_the_turn(self):
        left, right = ActorWorld(needs=object()), ActorWorld(needs=object())
        left.revenue._memo["assessments"] = ["kept"]
        self.assertEqual(right.revenue._memo, {})

    def test_every_part_the_world_lists_is_built_over_that_world(self):
        world = ActorWorld(needs=object())
        for name in ActorWorld.PARTS:
            self.assertIs(getattr(world, name).world, world, name)

    def test_a_name_that_is_not_a_part_is_an_attribute_error(self):
        with self.assertRaises(AttributeError):
            ActorWorld(needs=object()).not_a_part


if __name__ == "__main__":
    unittest.main()

"""Complaint 497: the entry year's shared grouping of crews by recipe gives the lists of the per-call read it replaced.
Called beside a copy of the plain read on random producers; no game."""

QUICK_TOPIC = True

import random
import types
import unittest

from sim.economy import entry_practice


def plain_crews(producers, recipe_id):
    return [each.crew_runs for _name, each in sorted(producers.items()) if each.recipe_id == recipe_id]


class SharedCrewsAreThePlainRead(unittest.TestCase):

    def test_each_recipe_gets_the_plain_list_and_the_scope_ends(self):
        rng = random.Random(3)
        for _round in range(40):
            producers = {"producer:%d" % rng.randrange(10 ** 6): types.SimpleNamespace(
                recipe_id=rng.choice("abcd"), crew_runs={"t": rng.uniform(1, 99)}) for _ in range(rng.randrange(0, 30))}
            with entry_practice.shared_crews(producers):
                crews = entry_practice.crews_of_recipe(producers)
                for recipe_id in "abcde":
                    self.assertEqual(crews(recipe_id), plain_crews(producers, recipe_id))
            producers["producer:new"] = types.SimpleNamespace(recipe_id="a", crew_runs={})
            self.assertEqual(entry_practice.crews_of_recipe(producers)("a"), plain_crews(producers, "a"))

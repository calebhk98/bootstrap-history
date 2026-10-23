"""A typo in explicit scenario data must fail fast, not degrade into a different opening state: the declared starting
technologies are returned whole when all are in the tree, and refused naming the unknown ones when any is not.
`starting_techs.declared_starting_techs` is called on a built civilisation record and tree. `grant_starting_techs` makes them done
and granted, and nothing else."""
QUICK_TOPIC = True

import unittest

from types import SimpleNamespace

from sim.engine.starting_techs import declared_starting_techs, grant_starting_techs

NODES = {"fire": {}, "bronze": {}, "iron": {}}


class DeclaredStartingTechsTests(unittest.TestCase):
    def test_the_declared_technologies_come_back_whole(self):
        civ = {"id": "test_civ", "starting_techs": ["fire", "bronze"]}
        self.assertEqual(list(declared_starting_techs(civ, NODES)), ["fire", "bronze"])

    def test_a_civilisation_declaring_none_opens_knowing_none(self):
        self.assertEqual(list(declared_starting_techs({"id": "test_civ", "starting_techs": []}, NODES)), [])

    def test_an_unknown_technology_is_refused_naming_it_and_the_civilisation(self):
        civ = {"id": "test_civ", "starting_techs": ["fire", "not_a_real_node", "also_missing"]}
        with self.assertRaises(ValueError) as refused:
            declared_starting_techs(civ, NODES)
        message = str(refused.exception)  # presentation: the refusal names what is wrong
        self.assertIn("not_a_real_node", message)
        self.assertIn("also_missing", message)
        self.assertIn("test_civ", message)
        self.assertNotIn("fire", message)


class GrantStartingTechsTests(unittest.TestCase):
    def test_the_declared_technologies_are_done_and_granted_and_nothing_else_is(self):
        projects = SimpleNamespace(done={"base"}, granted=set())
        grant_starting_techs(projects, ["fire", "bronze"], lambda: None)
        self.assertEqual(projects.done, {"base", "fire", "bronze"})
        self.assertEqual(projects.granted, {"fire", "bronze"})

    def test_the_change_is_announced_once_for_each_technology(self):
        announced = []
        grant_starting_techs(SimpleNamespace(done=set(), granted=set()), ["fire", "bronze"], lambda: announced.append(1))
        self.assertEqual(len(announced), 2)


if __name__ == "__main__":
    unittest.main()

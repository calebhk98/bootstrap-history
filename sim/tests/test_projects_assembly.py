"""The projects module in the shipped module set: it assembles (every view it reads and command it sends has a provider),
and a mod adds a start check by providing to `extra_start_checks` or removes one by a layer over the module's
`START_CHECKS`. No game is built: the assembly is made from the shipped specs alone."""
QUICK_TOPIC = True

import unittest

from sim.assembly.api import Operations, assemble
from sim.engine.game_assembly import shipped_specs
from sim.projects.api import START_CHECKS, Bribe, PostBounty, StartProject, StopProject


def mod_check(node_id, node, ignore_trade, memo, why):
    return False, "the mod forbids it"


class WithoutArrears:
    """A mod's layer over the module: the start test without the arrears check."""
    START_CHECKS = tuple(check for check in START_CHECKS if check.cause != "arrears")


class ProjectsInTheShippedSet(unittest.TestCase):
    def test_every_read_and_send_of_the_module_has_a_provider(self):
        assembly = assemble(shipped_specs())
        self.assertIn("projects", assembly.modules)
        self.assertEqual(assembly.view_owner["start_check"], "projects")
        self.assertEqual({assembly.command_owner[command] for command in (StartProject, StopProject, PostBounty, Bribe)}, {"projects"})

    def test_a_mod_provides_a_start_check_and_the_module_asks_it(self):
        assembly = assemble(shipped_specs(), [Operations("mymod", provided={"extra_start_checks": (mod_check,)})])
        point = assembly.modules["projects"].needs.extra_start_checks
        self.assertEqual(point("a", {}, False, None, True), (False, "the mod forbids it"))

    def test_with_no_mod_the_point_has_no_opinion(self):
        point = assemble(shipped_specs()).modules["projects"].needs.extra_start_checks
        self.assertIsNone(point("a", {}, False, None, True))

    def test_a_layer_over_the_module_removes_a_check_from_the_test(self):
        assembly = assemble(shipped_specs(), [Operations("mymod", layers={"projects": (WithoutArrears,)})])
        projects = assembly.modules["projects"]
        self.assertNotIn("arrears", [check.cause for check in projects.START_CHECKS])
        self.assertNotIn("arrears", projects._own_checks)
        self.assertEqual(len(projects.START_CHECKS), len(START_CHECKS) - 1)

    def test_the_shipped_module_still_has_every_check(self):
        projects = assemble(shipped_specs()).modules["projects"]
        self.assertEqual(projects.START_CHECKS, START_CHECKS)


if __name__ == "__main__":
    unittest.main()

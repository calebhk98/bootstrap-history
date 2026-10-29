"""Complaint 120: starting a project with the precaution adds the quoted cost to its bill and the quoted hours to its founder
hours and marks it; one a node does not offer is refused before anything starts. `begin_project` and `start_project`
called once each on the projects module built with the precaution's figures (extra cost, extra hours, whether a node offers
one) answered by recorders. The figures themselves are test_risk_precaution."""
import unittest

from sim.projects.api import SettleProjectMaterials, StartProject
from sim.tests import module_harness, projects_host

QUICK_TOPIC = True
UNDER_TEST = {"start_project"}

BILL = 1000.0
HOURS = 200.0
NODE = {"name": "Heat", "ph": HOURS, "lab": {"smith": 5.0}, "mechanics": {"precaution": {"kind": "pilot_plant"}}}
PLAIN = {"name": "Plain", "ph": HOURS, "lab": {"smith": 5.0}, "mechanics": {}}
EXTRA_COST, EXTRA_HOURS = 50.0, 7.0


def game(**views):
    """The module and the raw project state and order it writes."""
    state = projects_host.projects_state()
    order = ["plain", "declared"]
    module = projects_host.build(
        answers={SettleProjectMaterials: (BILL, 0.0)}, tree={"declared": NODE, "plain": PLAIN}, projects_record=state,
        order=order, project_cost=lambda node_id: BILL, start_refusal=lambda node_id: None)
    module.effective_risk = lambda node_id, precaution=None: 0.4
    module.calendar_floor = lambda node_id: 3.0
    module.precaution_extra_cost = lambda node_id, bill: EXTRA_COST
    module.precaution_extra_hours = lambda node_id: EXTRA_HOURS
    for name, value in views.items():
        setattr(module, name, value)
    return module, state, module.world


def begun(precaution):
    module, state, world = game()
    outcome = module.begin_project("declared", precaution)
    return world.order, outcome, state.active["declared"]


class BeginProject(unittest.TestCase):

    def test_the_plain_start_has_the_plain_bill_and_hours_and_no_mark(self):
        _order, outcome, record = begun(False)
        self.assertEqual(outcome, "begun")
        self.assertEqual((record["bill"], record["ph_left"]), (BILL, HOURS))
        self.assertNotIn("precaution", record)

    def test_the_bought_start_adds_the_quoted_cost_to_the_bill_and_the_quoted_hours_to_the_founder_hours(self):
        _order, _outcome, record = begun(True)
        self.assertEqual(record["bill"], BILL + EXTRA_COST)
        self.assertEqual(record["ph_left"], HOURS + EXTRA_HOURS)

    def test_the_bought_start_is_marked_so_the_dice_use_the_lowered_chance(self):
        _order, _outcome, record = begun(True)
        self.assertIs(record["precaution"], True)

    def test_the_money_still_to_pay_is_the_whole_bill_with_the_precaution(self):
        _order, _outcome, record = begun(True)
        self.assertAlmostEqual(record["cost_left"], record["bill"])

    def test_the_project_goes_to_the_front_of_the_order(self):
        order, _outcome, _record = begun(True)
        self.assertEqual(order[0], "declared")


class StartProjectRefusesAnUnofferedPrecaution(unittest.TestCase):

    def test_a_node_that_offers_none_is_refused_and_nothing_starts(self):
        module, state, _order = game(precaution_spec=lambda node_id: None)
        started, why = module.start_project(StartProject("plain", precaution=True))
        self.assertFalse(started)
        self.assertTrue(why)
        self.assertEqual(state.active, {})
        self.assertEqual([type(command) for command in module_harness.sent(module)], [])


if __name__ == "__main__":
    unittest.main()

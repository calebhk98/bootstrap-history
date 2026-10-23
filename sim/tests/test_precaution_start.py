"""Complaint 120: starting a project with the precaution adds the quoted cost to its bill and the quoted hours to its founder
hours and marks it; one a node does not offer is refused before anything starts. `begin_seat_project` and `start_project`
called on a stand-in game that holds one declared node (no game is built). The figures themselves are test_risk_precaution."""
import unittest
from types import SimpleNamespace

from sim.engine import projects_precaution as rules
from sim.engine.projects_starting import StartingMixin

QUICK_TOPIC = True

BILL = 1000.0
HOURS = 200.0
NODE = {"name": "Heat", "ph": HOURS, "lab": {"smith": 5.0}, "mechanics": {"precaution": {"kind": "pilot_plant"}}}
PLAIN = {"name": "Plain", "ph": HOURS, "lab": {"smith": 5.0}, "mechanics": {}}


class _Game(StartingMixin):

    def __init__(self):
        self.nodes = {"declared": NODE, "plain": PLAIN}
        self.order = ["plain", "declared"]
        self.state = SimpleNamespace(
            projects=SimpleNamespace(paid_towards={}, mothballed=set(), active={}),
            household=SimpleNamespace(log=[]), scenario=SimpleNamespace(year=100))
        self.begun_through_research = []

    def project_cost(self, node_id):
        return BILL

    def rebuild_work_factor(self, node_id):
        return 1.0

    def mechanic(self, node_id, name):
        return self.nodes[node_id]["mechanics"].get(name)

    def settle_project_materials(self, node_id):
        return BILL, 0.0

    def initialize_project(self, node_id, spent, cost_left, bill):
        self.state.projects.active[node_id] = {"spent": spent, "cost_left": cost_left, "bill": bill, "ph_left": self.nodes[node_id]["ph"]}

    def effective_risk(self, node_id, precaution=None):
        return 0.4

    def calendar_floor(self, node_id):
        return 3.0

    def start_refusal(self, node_id):
        return None


def begun(precaution):
    game = _Game()
    outcome = game.begin_seat_project("declared", precaution)
    return game, outcome, game.state.projects.active["declared"]


class BeginSeatProject(unittest.TestCase):

    def test_the_plain_start_has_the_plain_bill_and_hours_and_no_mark(self):
        _game, outcome, record = begun(False)
        self.assertEqual(outcome, "begun")
        self.assertEqual((record["bill"], record["ph_left"]), (BILL, HOURS))
        self.assertNotIn("precaution", record)

    def test_the_bought_start_adds_the_quoted_cost_to_the_bill_and_the_quoted_hours_to_the_founder_hours(self):
        game, _outcome, record = begun(True)
        self.assertAlmostEqual(record["bill"] - BILL, rules.extra_cost(game, "declared", BILL))
        self.assertAlmostEqual(record["ph_left"] - HOURS, rules.extra_hours(game, "declared"))
        self.assertGreater(record["bill"], BILL)
        self.assertGreater(record["ph_left"], HOURS)

    def test_the_bought_start_is_marked_so_the_dice_use_the_lowered_chance(self):
        _game, _outcome, record = begun(True)
        self.assertIs(record["precaution"], True)

    def test_the_money_still_to_pay_is_the_whole_bill_with_the_precaution(self):
        _game, _outcome, record = begun(True)
        self.assertAlmostEqual(record["cost_left"], record["bill"])

    def test_the_project_goes_to_the_front_of_the_order(self):
        game, _outcome, _record = begun(True)
        self.assertEqual(game.order[0], "declared")


class StartProjectRefusesAnUnofferedPrecaution(unittest.TestCase):

    def test_a_node_that_offers_none_is_refused_and_nothing_starts(self):
        game = _Game()
        started, why = game.start_project("plain", precaution=True)
        self.assertFalse(started)
        self.assertTrue(why)
        self.assertEqual(game.state.projects.active, {})


if __name__ == "__main__":
    unittest.main()

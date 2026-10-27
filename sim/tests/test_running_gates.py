"""A node can require that a built work is running, not merely known (Complaint 133).

`requires_running` on a node lists work ids that must be built and open. It gates beginning the
dependent, its effects while the work is shut, and a dependent that is open when the work closes.
A work others rely on does not get the softlock exemption from shedding in arrears."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.state import ProjectsState

from sim.engine import validate_running_gates
from sim.reporting.api import RecordEvent
from sim.tests import module_harness, production_host, projects_host
from sim.knowledge import rules as knowledge_rules

GRID, LAMP, TRAM = "grid", "lamp", "tram"


def _nodes():
    return {
        GRID: {"id": GRID, "pre": [], "up": 10.0, "rev": 0.0},
        LAMP: {"id": LAMP, "pre": [GRID], "up": 2.0, "rev": 1.0, "requires_running": [GRID]},
        TRAM: {"id": TRAM, "pre": [LAMP], "up": 2.0, "rev": 1.0, "requires_running": [LAMP]},
        "depot": {"id": "depot", "pre": [], "up": 1.0, "rev": 0.0, "requires_ways": {"rail": 50.0}},
        "lore": {"id": "lore", "pre": [GRID], "up": 0.0, "rev": 0.0, "requires_running": [GRID]},
    }


class _Host:
    """The projects module over a record of what is built and running, with production answering what runs."""

    def __init__(self, done, operating):
        self.nodes = _nodes()
        self.state = SimpleNamespace(projects=ProjectsState(done=set(done), granted=set()), scenario=SimpleNamespace(year=100))
        self.state.projects.operating = set(operating)
        self.built_km = {"rail": 0.0}
        self.production = production_host.build(self)
        self.module = projects_host.build(
            tree=self.nodes, legacy_projects=self.state.projects, techniques_held=self.state.projects.done,
            operating=lambda: self.state.projects.operating, running=self.production.running, is_venture=self.production.is_venture)
        self.module._built_way_km = lambda way: self.built_km.get(way, 0.0)

    def running(self, node_id):
        return self.production.running(node_id)

    def __getattr__(self, name):
        return getattr(self.module, name)

    def on_road_to_goal(self, node_id):
        return True


def _host(grid_open=True, lamp_open=True, tram_open=True):
    operating = {name for name, flag in ((GRID, grid_open), (LAMP, lamp_open), (TRAM, tram_open)) if flag}
    return _Host({GRID, LAMP, TRAM, "lore"}, operating)


class RunningGateTests(unittest.TestCase):

    def test_a_knowledge_dependent_stops_counting_while_the_work_is_shut(self):
        self.assertTrue(_host(grid_open=True).running("lore"))
        self.assertFalse(_host(grid_open=False).running("lore"))

    def test_an_unbuilt_work_leaves_the_gate_unmet(self):
        host = _host()
        host.state.projects.done.discard(GRID)
        self.assertEqual(host.unmet_running_gates(LAMP), [GRID])

    def test_a_node_without_the_field_is_unaffected(self):
        host = _host(grid_open=False)
        self.assertEqual(host.unmet_running_gates(GRID), [])
        self.assertFalse(host.running(GRID))

    def test_starting_is_refused_with_the_remedy_while_the_work_is_shut(self):
        host = _host(grid_open=False)
        verdict = host._check_running_gates(LAMP, host.nodes[LAMP], False, None, True)
        self.assertFalse(verdict[0])
        self.assertIn("open %s" % GRID, verdict[1])
        self.assertIsNone(_host()._check_running_gates(LAMP, _nodes()[LAMP], False, None, True))

    def test_opening_a_dependent_is_refused_while_its_work_is_shut(self):
        self.assertIn(GRID, _host(grid_open=False, lamp_open=False).running_gate_refusal(LAMP))
        self.assertIsNone(_host(lamp_open=False).running_gate_refusal(LAMP))


class WayGateTests(unittest.TestCase):

    def test_a_node_waits_for_the_length_of_way_it_names(self):
        host = _host()
        host.state.projects.done.add("depot")
        host.state.projects.operating.add("depot")
        host.built_km = {"rail": 10.0}
        self.assertEqual(host.ways_short("depot"), {"rail": 40.0})
        self.assertFalse(host.running("depot"))
        host.built_km = {"rail": 60.0}
        self.assertEqual(host.ways_short("depot"), {})
        self.assertTrue(host.running("depot"))

    def test_the_start_refusal_says_how_much_is_short(self):
        host = _host()
        host.built_km = {"rail": 10.0}
        verdict = host._check_running_gates("depot", host.nodes["depot"], False, None, True)
        self.assertFalse(verdict[0])
        self.assertIn("rail", verdict[1])
        self.assertIn("40", verdict[1])

    def test_a_bad_way_requirement_is_named(self):
        nodes = _nodes()
        nodes["depot"]["requires_ways"] = {"rail": -1}
        self.assertTrue(any("rail" in error for error in validate_running_gates.check_running_gates(nodes)))


class LapseTests(unittest.TestCase):

    def test_closing_the_work_closes_what_depends_on_it_down_the_chain(self):
        host = _host()
        host.close_work(GRID, host.CLOSED_BY_CHOICE)
        self.assertEqual(host.state.projects.operating, set())
        self.assertEqual(host.closure_of(LAMP)["reason"], host.CLOSED_GATE_LAPSED)
        self.assertEqual(host.closure_of(TRAM)["reason"], host.CLOSED_GATE_LAPSED)
        self.assertEqual(host.closure_of(GRID)["reason"], host.CLOSED_BY_CHOICE)

    def test_closing_a_dependent_leaves_its_work_running(self):
        host = _host()
        host.close_work(TRAM, host.CLOSED_BY_CHOICE)
        self.assertEqual(host.state.projects.operating, {GRID, LAMP})

    def test_the_yearly_check_closes_a_dependent_whose_work_was_forgotten(self):
        host = _host()
        host.state.projects.done.discard(GRID)
        host.state.projects.operating.discard(GRID)
        self.assertEqual(host.close_lapsed_dependents(101), [LAMP, TRAM])
        self.assertEqual(host.close_lapsed_dependents(101), [])

    def test_the_closure_is_logged_for_the_player(self):
        host = _host()
        host.close_work(GRID, host.CLOSED_BY_CHOICE)
        events = [command for command in module_harness.sent(host.module) if isinstance(command, RecordEvent)]
        self.assertTrue(any(event.kind == "work_closed_gate_lapsed" and event.facts["work"] == LAMP for event in events))


class ReliedOnWorkTests(unittest.TestCase):

    def test_a_work_others_need_running_is_named_and_a_plain_one_is_not(self):
        host = _host()
        self.assertTrue(host.relied_on_running(GRID))
        self.assertTrue(host.relied_on_running(LAMP))
        self.assertFalse(host.relied_on_running(TRAM))


    def test_the_road_to_the_goal_no_longer_shields_a_work_others_rely_on(self):
        host = _host()
        for node_id, expected in ((GRID, False), (TRAM, True)):
            self.assertEqual(knowledge_rules.never_abandon(False, host.relied_on_running(node_id), host.on_road_to_goal(node_id)),
                             expected)


class ValidationTests(unittest.TestCase):

    def test_clean_data_passes(self):
        self.assertEqual(validate_running_gates.check_running_gates(_nodes()), [])

    def test_an_unknown_id_is_named(self):
        nodes = _nodes()
        nodes[LAMP]["requires_running"] = ["nowhere"]
        self.assertTrue(any("nowhere" in error for error in validate_running_gates.check_running_gates(nodes)))

    def test_a_node_that_cannot_run_is_named(self):
        nodes = _nodes()
        nodes[TRAM]["requires_running"] = ["lore"]
        self.assertTrue(any("lore" in error for error in validate_running_gates.check_running_gates(nodes)))

    def test_a_cycle_is_named(self):
        nodes = _nodes()
        nodes[GRID]["requires_running"] = [TRAM]
        self.assertTrue(any("cycle" in error for error in validate_running_gates.check_running_gates(nodes)))

    def test_hours_fields_make_a_venture_before_prices_are_known(self):
        nodes = {"a": {"up_hours": 5.0, "rev_hours": 0},
                 "b": {"up_hours": 0, "rev_hours": 0, "requires_running": ["a"]}}
        self.assertEqual(validate_running_gates.check_running_gates(nodes), [])


if __name__ == "__main__":
    unittest.main()

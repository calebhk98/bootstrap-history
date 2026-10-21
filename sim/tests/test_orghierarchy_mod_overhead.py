"""The organisational hierarchy mod charges the apex's own direct reports against the directed-hours pool (Complaint 633).

The mod's pure rule is called with built inputs; its `register` is run against a recording stand-in for the mod API."""
QUICK_TOPIC = True

import types
import unittest

from sim.tests.mod_files import RecordingApi, load_mod_file

MOD = "bh_orghierarchy_r4k8"
HIERARCHY = load_mod_file(MOD, "hierarchy_commands.py")
PARAMETERS = HIERARCHY.load_parameters()
MANAGER_HOURS = 2000.0
COORDINATION = PARAMETERS["coordination_hours_per_report_per_year"]["value"]


class ApexOverhead(unittest.TestCase):
    def test_with_no_managers_the_apex_directs_every_worker(self):
        hours = HIERARCHY.apex_overhead_hours(5.0, MANAGER_HOURS, PARAMETERS, set(), 0)
        self.assertEqual(hours, 5 * COORDINATION)

    def test_hired_managers_take_reports_off_the_apex(self):
        workers = 100.0
        plan = HIERARCHY.plan(workers, MANAGER_HOURS, PARAMETERS, set())
        none = HIERARCHY.apex_overhead_hours(workers, MANAGER_HOURS, PARAMETERS, set(), 0)
        some = HIERARCHY.apex_overhead_hours(workers, MANAGER_HOURS, PARAMETERS, set(), 3)
        full = HIERARCHY.apex_overhead_hours(workers, MANAGER_HOURS, PARAMETERS, set(), plan["managers_total"])
        self.assertGreater(none, some)
        self.assertGreater(some, full)
        self.assertEqual(full, plan["apex_direct_reports"] * COORDINATION)

    def test_a_known_record_keeping_technology_cuts_the_hours(self):
        node = next(iter(PARAMETERS["channels"]["record_keeping"]["factor_when_known"]))
        without = HIERARCHY.apex_overhead_hours(5.0, MANAGER_HOURS, PARAMETERS, set(), 0)
        with_it = HIERARCHY.apex_overhead_hours(5.0, MANAGER_HOURS, PARAMETERS, {node}, 0)
        self.assertLess(with_it, without)

    def test_register_charges_the_overhead_through_the_hook(self):
        api = RecordingApi(MOD)
        HIERARCHY.register(api)
        (_name, (function,), _fields), = api.registered("director_overhead")
        sim = types.SimpleNamespace(employees={"scribe": 5.0}, done=set(), cfg={"director_hours_per_year": MANAGER_HOURS},
                                    state=types.SimpleNamespace(interface={}))
        self.assertEqual(function(sim), 5 * COORDINATION)


if __name__ == "__main__":
    unittest.main()

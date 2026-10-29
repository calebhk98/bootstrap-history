"""The ventures module's change counters: what a seat has open and the sizes of its institutions are counted where the module
applies the change, and the views carry the count to the memos keyed on them. Called on the module over plain values; no game."""
QUICK_TOPIC = True

import types
import unittest

from sim.tests import ventures_host
from sim.ventures.api import NoteOperatingChanged

SCHOOL = {"school": {"id": "school", "up": 2.0, "rev": 1.0}}


def school_module(operating=()):
	record = ventures_host.projects_record(done={"school"}, operating=set(operating),
	                                       business=types.SimpleNamespace(
	                                           open_plant=lambda node_id, year: None, set_size=lambda node_id, size: None,
	                                           note_opened_year_if_unknown=lambda node_id, year: None))
	return ventures_host.build(
		legacy_projects=record, tree_nodes=SCHOOL, is_venture=lambda node_id: True,
		capability_sets=(frozenset(), frozenset({"school"}), {}), institution_unit_ceiling=lambda node_id: 5.0,
		venture_ramp=lambda node_id: 1.0)


class OperatingVersionTests(unittest.TestCase):
	def test_a_note_that_the_operating_set_changed_moves_the_operating_version(self):
		module = school_module()
		before = module.operating_version()
		module.apply_note_operating_changed(NoteOperatingChanged())
		self.assertNotEqual(module.operating_version(), before)

	def test_the_other_counter_does_not_move_with_it(self):
		module = school_module()
		before = module.institution_units_version()
		module.apply_note_operating_changed(NoteOperatingChanged())
		self.assertEqual(module.institution_units_version(), before)

	def test_a_seat_that_was_not_noted_keeps_its_version(self):
		module = school_module()
		module.clock.act_as("other")
		before = module.operating_version()
		module.clock.act_as("founder")
		module.apply_note_operating_changed(NoteOperatingChanged())
		module.clock.act_as("other")
		self.assertEqual(module.operating_version()[2:], before[2:])


class InstitutionUnitsVersionTests(unittest.TestCase):
	def test_expanding_an_open_institution_moves_the_units_version(self):
		module = school_module(operating={"school"})
		before = module.institution_units_version()
		opened, _reply = module._expand_institution("school", 1.0, pay=False)
		self.assertTrue(opened)
		self.assertNotEqual(module.institution_units_version(), before)

	def test_a_refused_expansion_leaves_the_units_version(self):
		module = ventures_host.build(
			legacy_projects=ventures_host.projects_record(operating={"school"}), tree_nodes=SCHOOL)
		before = module.institution_units_version()
		opened, _reply = module._expand_institution("school", 1.0, pay=False)
		self.assertFalse(opened)
		self.assertEqual(module.institution_units_version(), before)

	def test_opening_a_scalable_institution_moves_the_units_version_and_not_the_operating_one(self):
		module = school_module()
		units_before, operating_before = module.institution_units_version(), module.operating_version()
		opened, _reply = module.open_venture("school", pay=False, units=0.5)
		self.assertTrue(opened)
		self.assertNotEqual(module.institution_units_version(), units_before)
		self.assertEqual(module.operating_version(), operating_before)


if __name__ == "__main__":
	unittest.main()

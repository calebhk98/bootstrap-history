"""The founder's death record is read through the game's properties over the founder's saved state (sim/engine/core_properties.py)."""
import unittest
from types import SimpleNamespace

from sim.engine.core_properties import ForwardingPropertiesMixin

QUICK_TOPIC = True


def game(**founder_fields):
	return SimpleNamespace(state=SimpleNamespace(acting_record=SimpleNamespace(founder=SimpleNamespace(**founder_fields))))


class FounderDeathRecord(unittest.TestCase):

	def test_the_age_at_death_is_read_from_the_founders_state(self):
		self.assertEqual(ForwardingPropertiesMixin._founder_death_aged.fget(game(_founder_death_aged=61)), 61)

	def test_the_year_of_death_is_read_from_the_founders_state(self):
		self.assertEqual(ForwardingPropertiesMixin._founder_death_year.fget(game(_founder_death_year=140)), 140)

	def test_an_unrecorded_death_is_an_attribute_error_so_a_defaulted_read_answers_none(self):
		with self.assertRaises(AttributeError):
			ForwardingPropertiesMixin._founder_death_aged.fget(game())


if __name__ == "__main__":
	unittest.main()

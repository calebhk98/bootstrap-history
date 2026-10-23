"""Stage 3b of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md: the yearly rules are one `Business.review`.

The loss rule of a firm is tested on a built world: a business that loses money for consecutive years closes. The
founder's seat and the creditors' seizure are test_seat_creditors_rule."""

QUICK_TOPIC = True
import unittest

from sim.agents import business_review
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Business
from sim.agents.tuning import EXIT_LOSS_YEARS

from .agents_fake_world import FakeWorld, make_node


def a_firm_running(entry_key):
	world = FakeWorld(year=50)
	world.nodes[entry_key] = make_node(entry_key, hours=100.0, revenue=10.0, upkeep=1.0)
	registry = ActorRegistry(ActorsState(home_country="home"))
	firm = registry.add("firm:1", ActorRecord(kind="firm", founded_year=0, business=Business.running([entry_key], opened_year=0)))
	return world, firm


def years_until_closed(business, owner, world, margin, limit=3 * EXIT_LOSS_YEARS):
	"""Tally `margin` year after year, reviewing the loss rule each time; the number of years until a plant is closed."""
	entry_key = next(iter(business.entry_keys()))
	for years in range(1, limit + 1):
		business.note_year(entry_key, margin)
		closed = business.review(owner, world, rules=(business_review.LOSS_MAKING,))
		if closed:
			return years, closed
	return None, []


class LossRuleIsOneRule(unittest.TestCase):
	def test_a_firm_closes_a_plant_after_the_shared_run_of_loss_years(self):
		world, firm = a_firm_running("shop")
		years, closed = years_until_closed(firm.business, firm, world, margin=-1.0)
		self.assertEqual(years, EXIT_LOSS_YEARS)
		self.assertEqual([(closure.entry_key, closure.reason) for closure in closed], [("shop", business_review.LOSS_MAKING)])
		self.assertIsNone(firm.business.plant_of("shop"))

	def test_a_profitable_year_restarts_the_count(self):
		world, firm = a_firm_running("shop")
		for margin in [-1.0] * (EXIT_LOSS_YEARS - 1) + [1.0] + [-1.0] * (EXIT_LOSS_YEARS - 1):
			firm.business.note_year("shop", margin)
			self.assertEqual(firm.business.review(firm, world, rules=(business_review.LOSS_MAKING,)), [])
		self.assertEqual(firm.business.plant_of("shop").loss_years, EXIT_LOSS_YEARS - 1)


if __name__ == "__main__":
	unittest.main()

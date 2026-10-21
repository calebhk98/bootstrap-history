"""Complaint 657: a higher rate is a cost to the taxpayer, and the taxpayer's own rule decides with what is left.
A harvest tax lowers the farm effort the price ratio supports; a land tax lowers the rent an owner keeps and
makes marginal holdings (many tenancies, thin net rent) a loss that the owner lets go of."""
import unittest

from sim.agents import tax_burden
from sim.economy import titles
from sim.labour import farm_intake
from sim.tests.agents_fake_world import FakeWorld
from sim.tests.test_economy_title_counterforces import ManagementCostTests
from sim.tests.test_economy_titles import LANDLORD, MONEY

QUICK_TOPIC = True


class TaxedWorld(FakeWorld):
	def __init__(self, forms, rate=0.05):
		super().__init__()
		self.forms, self.rate = forms, rate

	def revenue_forms(self):
		return self.forms

	def held_tiles(self):
		return ["a", "b"]

	def arable_share(self, tiles):
		return 0.5 * len(set(tiles) & {"a", "b"})


def harvest_form(rate, **extra):
	return dict({"form": "grain_tax", "basis": "harvest", "rate": rate, "paid_in": "wheat_kg"}, **extra)


class HarvestTaxTests(unittest.TestCase):
	def test_the_share_taken_is_the_rate_of_the_forms_on_the_harvest(self):
		self.assertAlmostEqual(tax_burden.harvest_share_taken(TaxedWorld([harvest_form(0.1)])), 0.1)
		self.assertAlmostEqual(tax_burden.harvest_share_taken(TaxedWorld([harvest_form(0.1, tiles=["a"])])), 0.05)
		poll = {"form": "poll", "basis": "adult_labour_years", "rate": 0.2}
		self.assertEqual(tax_burden.harvest_share_taken(TaxedWorld([poll])), 0.0)

	def test_officials_who_reach_less_take_less(self):
		world = TaxedWorld([harvest_form(0.2)])
		world.collectible = 0.5
		self.assertAlmostEqual(tax_burden.harvest_share_taken(world), 0.1)

	def test_a_higher_harvest_tax_lowers_the_farm_effort_the_price_ratio_supports(self):
		ratio = 1.05      # farming pays a little over the wage; hands stay at most as many as today
		efforts = [farm_intake.kept_farm_workers(
			100.0, 150.0, 150.0, farm_intake.value_over_wage_after_tax(ratio, share), 0.5) for share in (0.0, 0.1, 0.3)]
		self.assertGreater(efforts[0], efforts[1])
		self.assertGreater(efforts[1], efforts[2])

	def test_a_tax_that_takes_the_ratio_below_one_lets_hands_go(self):
		ratio = farm_intake.value_over_wage_after_tax(1.2, 0.5)
		self.assertLess(farm_intake.kept_farm_workers(100.0, 150.0, 150.0, ratio, 0.5), 100.0)
		self.assertIsNone(farm_intake.value_over_wage_after_tax(None, 0.5))


class LandTaxTests(unittest.TestCase):
	def test_a_higher_land_tax_lowers_the_rent_the_owner_keeps(self):
		low = TaxedWorld([{"form": "land", "basis": "land_value", "rate": 0.005}])
		high = TaxedWorld([{"form": "land", "basis": "land_value", "rate": 0.01}])
		self.assertAlmostEqual(tax_burden.land_tax_share_of_rent(low), 0.1)
		self.assertLess(tax_burden.after_tax_rent(100.0, tax_burden.land_tax_share_of_rent(high)),
						tax_burden.after_tax_rent(100.0, tax_burden.land_tax_share_of_rent(low)))
		rent_form = TaxedWorld([{"form": "rent", "basis": "land_rent", "rate": 0.3}])
		self.assertAlmostEqual(tax_burden.land_tax_share_of_rent(rent_form), 0.3)

	def test_a_higher_land_tax_makes_a_marginal_holding_a_loss_and_the_owner_lets_it_go(self):
		held = {}
		for share in (0.0, 0.6, 0.95):
			record, arable = ManagementCostTests("test_cost_share_rises_with_the_number_of_tenancies_and_a_lone_tenancy_is_free").lessor_world(6)
			titles.settle_tenancies(record, MONEY, arable, land_tax_share_of_rent=share)
			held[share] = sum(titles.holding(record, tile, LANDLORD) for tile in arable)
		self.assertGreater(held[0.0], 0.0)
		self.assertEqual(held[0.0], held[0.6])      # six tenancies cost 5% of the rent: a 60% tax still leaves a net rent
		self.assertEqual(held[0.95], 0.0)           # cost and tax together exceed the rent: every holding is let go

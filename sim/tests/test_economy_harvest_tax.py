"""Complaint 657: a grower nets the state's share of the harvest off what the harvest fetches. Plain functions, inputs written out."""
import unittest
from types import SimpleNamespace

from sim.agents import tax_burden
from sim.economy import harvest_tax
from sim.economy.households_hours_offered import plot_hours_kept
from sim.economy.types import Recipe

QUICK_TOPIC = True

GRAIN_RUN = Recipe(recipe_id="grow_grain", outputs={"grain": 100.0, "straw": 50.0}, inputs={}, labour_hours={"farmer": 50.0})


class KeptShare(unittest.TestCase):
	def test_a_grower_keeps_what_the_state_leaves_of_the_good(self):
		self.assertAlmostEqual(harvest_tax.kept_share("grain", {"grain": 0.2}), 0.8)

	def test_a_good_the_state_does_not_tax_is_kept_whole(self):
		self.assertEqual(harvest_tax.kept_share("straw", {"grain": 0.2}), 1.0)

	def test_a_take_above_all_leaves_nothing_and_below_nothing_leaves_all(self):
		self.assertEqual(harvest_tax.kept_share("grain", {"grain": 1.5}), 0.0)
		self.assertEqual(harvest_tax.kept_share("grain", {"grain": -0.5}), 1.0)


class NetRevenue(unittest.TestCase):
	PRICES = {"grain": 2.0, "straw": 1.0}

	def test_without_a_tax_it_is_the_revenue_of_the_run(self):
		self.assertAlmostEqual(harvest_tax.net_revenue_per_run(GRAIN_RUN, self.PRICES, {}), 250.0)

	def test_the_taxed_good_fetches_the_share_it_keeps(self):
		self.assertAlmostEqual(harvest_tax.net_revenue_per_run(GRAIN_RUN, self.PRICES, {"grain": 0.2}), 0.8 * 200.0 + 50.0)

	def test_net_prices_are_the_prices_times_the_kept_share(self):
		self.assertEqual(harvest_tax.net_output_prices(self.PRICES, {"grain": 0.25}), {"grain": 1.5, "straw": 1.0})

	def test_a_recipe_making_nothing_keeps_all_of_it(self):
		self.assertEqual(harvest_tax.kept_share_of_outputs({}, {"grain": 0.2}), 1.0)

	def test_outputs_weigh_by_quantity(self):
		self.assertAlmostEqual(harvest_tax.kept_share_of_outputs({"grain": 100.0, "straw": 100.0}, {"grain": 0.2}), 0.9)


class FarmHoursFallWithTheTax(unittest.TestCase):
	def test_a_lower_return_on_the_plot_keeps_fewer_hours_for_it_at_the_same_wage(self):
		free = plot_hours_kept(2000.0, 4.0, 2.0, 2000.0)
		taxed = plot_hours_kept(2000.0, 4.0, 2.0 * harvest_tax.kept_share("grain", {"grain": 0.3}), 2000.0)
		self.assertLess(taxed, free)


class ShareByMaterial(unittest.TestCase):
	"""agents' tax_burden.harvest_share_by_material: the shares the port hands the economy."""

	def world(self, forms):
		revenue = SimpleNamespace(revenue_forms=lambda: forms, held_tiles=lambda: set(), arable_share=lambda tiles: 1.0)
		return SimpleNamespace(quotes=SimpleNamespace(staple_material=lambda: "wheat_kg"), revenue=revenue,
							   collection=SimpleNamespace(collectible_share=lambda tiles: 0.5))

	def test_the_staple_and_each_material_a_harvest_form_is_paid_in_get_a_share_weighted_by_the_officials_reach(self):
		forms = [{"form": "levy", "basis": "harvest", "rate": 0.2, "paid_in": "barley_kg"},
				 {"form": "tithe", "basis": "harvest", "rate": 0.1}, {"form": "poll", "basis": "head", "rate": 0.3}]
		shares = tax_burden.harvest_share_by_material(self.world(forms))
		self.assertEqual(sorted(shares), ["barley_kg", "wheat_kg"])
		self.assertAlmostEqual(shares["barley_kg"], 0.15)
		self.assertAlmostEqual(shares["wheat_kg"], 0.05)

	def test_no_harvest_form_leaves_only_the_staple_at_nothing(self):
		self.assertEqual(tax_burden.harvest_share_by_material(self.world([])), {"wheat_kg": 0.0})

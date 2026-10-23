"""SMOKE (Complaint 507, stage 2): the Rome opening's prices are the cost of making each good at the opening wages, rate and
rent, and in hours of work do not depend on what the player holds. Builds two unopened games, no years. The fixture rules of the
opening's consistency are in test_opening_consistency_rule."""
import unittest

from sim.tests import harness


class OpeningSeedsAreCostsTests(unittest.TestCase):
    """The Rome opening's prices (Complaint 507 stage 2): the cost of making each good at the opening wages,
    rate and rent, and nothing of demand or of the player's money."""

    @classmethod
    def setUpClass(cls):
        from sim.engine import economy_port_costs, economy_port_setup
        from sim.labour.api import wage_provider
        cls.game = harness.unopened_sim()
        cls.opening = economy_port_setup.opening_values(cls.game)
        cls.costs = economy_port_costs
        cls.wage_provider = wage_provider

    def _cost_of_one_step(self, good):
        from sim.engine import long_run_costs, making_cost
        from sim.engine.prices import default_production_entries
        game, prices = self.game, self.opening["prices"]
        production = default_production_entries()
        techniques = frozenset(game.state.projects.granted) | frozenset(game.techniques_in_use())
        wage_of = self.costs.wage_function(game, production)
        rent_of = long_run_costs.opening_rent_of(techniques, wage_of, game.civ, production)
        made = making_cost.cost_of_making(good, techniques, prices.get, wage_of, self.opening["rate"], rent_of,
                                          production=production, civilization=game.civ)
        return made.unit_cost

    def test_the_staple_costs_what_its_recipe_bill_comes_to_at_the_opening_wages(self):
        staple = self.wage_provider.staple_material(self.game.civ)
        self.assertAlmostEqual(self.opening["prices"][staple] / self._cost_of_one_step(staple), 1.0, delta=0.25)

    def test_the_coin_metal_is_priced_at_its_cost_of_making(self):
        metal = self.wage_provider.coin_standard(self.game.civ)["material"]
        self.assertAlmostEqual(self.opening["prices"][metal] / self._cost_of_one_step(metal), 1.0, delta=0.25)

    def test_the_prices_in_hours_of_work_do_not_depend_on_what_the_player_holds(self):
        from sim.engine import economy_port_setup
        richer = economy_port_setup.opening_values(harness.unopened_sim(capital=1.0e9))
        unskilled = self.opening["unskilled_trade"]
        for good, price in sorted(self.opening["prices"].items()):
            self.assertAlmostEqual(richer["prices"][good] / richer["wages"][unskilled],
                                   price / self.opening["wages"][unskilled], places=9, msg=good)

    def test_a_good_the_economy_has_not_priced_is_seeded_at_a_cost_of_making_at_live_prices(self):
        from sim.engine import economy_port_late
        from sim.engine.prices import default_production_entries
        known = dict(self.opening["prices"])
        staple = self.wage_provider.staple_material(self.game.civ)
        gone = known.pop(staple)
        found = economy_port_late.late_goods_costs(self.game, known, [staple], frozenset(self.game.state.projects.granted),
                                                   default_production_entries())
        self.assertAlmostEqual(found[staple] / gone, 1.0, delta=0.25)


if __name__ == "__main__":
    unittest.main()

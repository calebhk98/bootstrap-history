"""merchant_volume_news: the volume of a market that merchants learn, with and without the demand left unmet."""

QUICK_TOPIC = True

import unittest

from sim.economy import merchant_volume_news, rule_sets

POTS_HERE, POTS_THERE, SALT_HERE = ("pot_kg", "here"), ("pot_kg", "there"), ("salt_kg", "here")
DELIVERED = {POTS_HERE: 500.0, POTS_THERE: 4.0}
UNMET = [(POTS_THERE, 300.0), (SALT_HERE, 20.0), (POTS_HERE, 0.0)]


class DeliveredAndUnmet(unittest.TestCase):
    def setUp(self):
        self.volumes = merchant_volume_news.delivered_and_unmet(DELIVERED, UNMET)

    def test_a_short_market_counts_what_its_buyers_went_without(self):
        self.assertEqual(self.volumes[POTS_THERE], 4.0 + 300.0)

    def test_a_market_that_met_its_demand_counts_its_deliveries(self):
        self.assertEqual(self.volumes[POTS_HERE], 500.0)

    def test_a_market_with_unmet_demand_and_no_delivery_is_counted(self):
        self.assertEqual(self.volumes[SALT_HERE], 20.0)

    def test_the_deliveries_given_are_not_changed(self):
        self.assertEqual(DELIVERED, {POTS_HERE: 500.0, POTS_THERE: 4.0})

    def test_nothing_unmet_gives_the_deliveries(self):
        self.assertEqual(merchant_volume_news.delivered_and_unmet(DELIVERED, []), DELIVERED)


class DeliveredAlone(unittest.TestCase):
    def test_the_deliveries_come_back_as_they_are(self):
        self.assertIs(merchant_volume_news.delivered_alone(DELIVERED, UNMET), DELIVERED)


class TheRuleSetsVolumes(unittest.TestCase):
    def test_search_learns_deliveries_and_clearing_adds_the_unmet_demand(self):
        self.assertIs(rule_sets.RULE_SETS[rule_sets.SEARCH].merchant_volumes, merchant_volume_news.delivered_alone)
        self.assertIs(rule_sets.RULE_SETS[rule_sets.CLEARING].merchant_volumes, merchant_volume_news.delivered_and_unmet)


if __name__ == "__main__":
    unittest.main()

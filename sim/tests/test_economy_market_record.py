"""The agent economy's record keeps what each market sold, left unsold and left unmet last year, saved with it."""
import json
import unittest

from sim.economy import api as economy_api
from sim.economy.record import EconomyRecord
from sim.tests import economy_fixture as fixture


class MarketRecordTests(unittest.TestCase):
    def setUp(self):
        self.economy = fixture.run(fixture.small_setup(), years=4)[0]

    def test_sold_is_the_traded_volume_of_the_good(self):
        volumes = economy_api.traded_volumes(self.economy)
        self.assertTrue(volumes)
        for good in volumes:
            self.assertAlmostEqual(economy_api.market_record(self.economy, good)["sold"], volumes[good])

    def test_unsold_and_unmet_are_never_negative(self):
        for good in economy_api.traded_volumes(self.economy):
            record = economy_api.market_record(self.economy, good)
            self.assertGreaterEqual(record["unsold"], 0.0)
            self.assertGreaterEqual(record["unmet"], 0.0)

    def test_a_good_nobody_trades_has_an_empty_record(self):
        self.assertEqual(economy_api.market_record(self.economy, "no_such_good"),
                         {"sold": 0.0, "unsold": 0.0, "unmet": 0.0})

    def test_every_market_that_has_a_volume_has_an_unsold_and_an_unmet_figure(self):
        self.assertEqual(set(self.economy.record.unsold), set(self.economy.record.volumes))
        self.assertEqual(set(self.economy.record.unmet), set(self.economy.record.volumes))

    def test_the_record_survives_a_save_and_load(self):
        saved = json.loads(json.dumps(self.economy.record.to_record()))
        loaded = EconomyRecord.from_record(saved)
        self.assertEqual(loaded.unsold, self.economy.record.unsold)
        self.assertEqual(loaded.unmet, self.economy.record.unmet)


if __name__ == "__main__":
    unittest.main()

"""The market record sums what each market of a good sold, left unsold and left unmet, over the good's areas, and the
record carries unsold and unmet through a save. The rule is called on a record built here, no year is run."""
QUICK_TOPIC = True
import json
import types
import unittest

from sim.economy import api as economy_api
from sim.economy.economy import Economy
from sim.economy.record import EconomyRecord
from sim.tests import economy_fixture as fixture


def economy_with(volumes, unsold, unmet):
    record = Economy(fixture.small_setup()).record
    record.volumes, record.unsold, record.unmet = dict(volumes), dict(unsold), dict(unmet)
    return types.SimpleNamespace(record=record)


VOLUMES = {"grain|north": 10.0, "grain|south": 5.0, "iron|north": 2.0}
UNSOLD = {"grain|north": 1.0, "grain|south": 0.0, "iron|north": 0.5}
UNMET = {"grain|north": 0.0, "grain|south": 3.0, "iron|north": 0.0}


class MarketRecordRuleTests(unittest.TestCase):
    def setUp(self):
        self.economy = economy_with(VOLUMES, UNSOLD, UNMET)

    def test_a_good_sums_over_its_areas_and_leaves_other_goods_out(self):
        self.assertEqual(economy_api.market_record(self.economy, "grain"), {"sold": 15.0, "unsold": 1.0, "unmet": 3.0})
        self.assertEqual(economy_api.market_record(self.economy, "iron"), {"sold": 2.0, "unsold": 0.5, "unmet": 0.0})

    def test_sold_is_the_traded_volume_of_the_good(self):
        volumes = economy_api.traded_volumes(self.economy)
        for good, volume in volumes.items():
            self.assertAlmostEqual(economy_api.market_record(self.economy, good)["sold"], volume)

    def test_a_good_nobody_trades_has_an_empty_record(self):
        self.assertEqual(economy_api.market_record(self.economy, "no_such_good"),
                         {"sold": 0.0, "unsold": 0.0, "unmet": 0.0})

    def test_the_record_survives_a_save_and_load(self):
        saved = json.loads(json.dumps(self.economy.record.to_record()))
        loaded = EconomyRecord.from_record(saved)
        self.assertEqual(loaded.unsold, UNSOLD)
        self.assertEqual(loaded.unmet, UNMET)
        self.assertEqual(loaded.volumes, VOLUMES)


if __name__ == "__main__":
    unittest.main()

"""`trade_book_in_coin`: the tonnes of a country's trade book stay, its values are counted in coin, whichever way it is read."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.markets import port_country

BOOK = {"wheat_kg": {"in_tonnes": 3.0, "in_value": 10.0, "out_tonnes": 1.0, "out_value": 4.0}}


class TradeBookInCoin(unittest.TestCase):
    def test_values_are_scaled_by_the_economys_coin_and_tonnes_are_not(self):
        with mock.patch.object(port_country, "coin_per_unit", lambda economy: 2.5), \
                mock.patch.object(port_country.country_figures, "trade_book", lambda economy, country: BOOK):
            book = port_country.trade_book_in_coin("economy", "han")
        self.assertEqual(book, {"wheat_kg": {"in_tonnes": 3.0, "in_value": 25.0, "out_tonnes": 1.0, "out_value": 10.0}})


if __name__ == "__main__":
    unittest.main()

"""The words for a civilisation's money come from its own file, not an engine table."""
import unittest

from sim.engine import data

CIVS = ["rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500", "england_1300",
        "sample_egypt_100bc_e7k2:egypt"]


class CurrencyWordsAreCivData(unittest.TestCase):
    def test_each_civ_declares_long_and_short_words(self):
        for name in CIVS:
            words = data.load_civ(name).get("currency_words") or {}
            self.assertTrue(words.get("long") and words.get("short"), name)

    def test_money_word_reads_the_civ_file(self):
        civ = {"currency": "invented shell", "currency_words": {"long": "shells", "short": "sh"}}
        self.assertEqual(data.money_word(civ), "shells")
        self.assertEqual(data.money_short(civ), "sh")

    def test_engine_holds_no_per_currency_table(self):
        self.assertFalse(hasattr(data, "MONEY_WORDS"))
        self.assertFalse(hasattr(data, "MONEY_SHORT_WORDS"))


if __name__ == "__main__":
    unittest.main()

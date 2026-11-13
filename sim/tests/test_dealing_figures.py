"""Complaint 931: the rules of a deal (patents, shares, offers) are functions of plain figures, written out here; the exchange applies them to
an actor's record and the seats module applies them to a seat's stored figures."""
QUICK_TOPIC = True

import unittest

from sim.agents import dealing_figures as figures


class Patents(unittest.TestCase):
    def test_a_right_released_leaves_the_book_and_the_taker_is_struck_from_its_licensees(self):
        book = {"loom": {"granted": 1, "expires": 9, "licensees": ["a", "b"]}, "kiln": {"granted": 2, "expires": 8, "licensees": []}}
        after, entry = figures.release_patent(book, "loom", "a")
        self.assertEqual((after, entry), ({"kiln": {"granted": 2, "expires": 8, "licensees": []}}, {"granted": 1, "expires": 9, "licensees": ["b"]}))
        self.assertIn("loom", book)

    def test_releasing_a_right_not_held_is_a_key_error(self):
        with self.assertRaises(KeyError):
            figures.release_patent({}, "loom", "a")

    def test_a_right_received_is_added_as_a_copy(self):
        entry = {"granted": 1, "expires": 9, "licensees": []}
        after = figures.receive_patent({"kiln": {}}, "loom", entry)
        entry["expires"] = 99
        self.assertEqual(after, {"kiln": {}, "loom": {"granted": 1, "expires": 9, "licensees": []}})

    def test_a_licensee_is_added_once(self):
        book = {"loom": {"licensees": ["a"]}}
        once = figures.add_licensee(book, "loom", "b")
        twice = figures.add_licensee(once, "loom", "b")
        self.assertEqual((once, twice, book), ({"loom": {"licensees": ["a", "b"]}}, {"loom": {"licensees": ["a", "b"]}}, {"loom": {"licensees": ["a"]}}))


class Shares(unittest.TestCase):
    def test_giving_shares_held_lowers_the_holding(self):
        self.assertEqual(figures.give_shares(0.0, {"firm:1": 0.5}, "firm:1", 0.25, False), (0.0, {"firm:1": 0.25}))

    def test_giving_all_of_a_holding_removes_it(self):
        self.assertEqual(figures.give_shares(0.0, {"firm:1": 0.5}, "firm:1", 0.5, False), (0.0, {}))

    def test_an_issuer_giving_its_own_equity_raises_what_it_has_issued(self):
        self.assertEqual(figures.give_shares(0.25, {"firm:1": 0.5}, "me", 0.25, True), (0.5, {"firm:1": 0.5}))

    def test_taking_shares_adds_to_the_holding(self):
        self.assertEqual(figures.take_shares(0.0, {"firm:1": 0.5}, "firm:1", 0.25, False), (0.0, {"firm:1": 0.75}))

    def test_an_issuer_buying_back_its_own_equity_lowers_what_it_has_issued_to_no_less_than_nothing(self):
        self.assertEqual(figures.take_shares(0.25, {}, "me", 0.125, True), (0.125, {}))
        self.assertEqual(figures.take_shares(0.25, {}, "me", 0.5, True), (0.0, {}))


class Offers(unittest.TestCase):
    def test_an_offer_is_kept_after_those_held(self):
        self.assertEqual(figures.keep_offer([{"id": "a#1"}], {"id": "b#1"}), [{"id": "a#1"}, {"id": "b#1"}])

    def test_an_offer_is_dropped_by_id(self):
        self.assertEqual(figures.drop_offer([{"id": "a#1"}, {"id": "b#1"}], "a#1"), [{"id": "b#1"}])

    def test_offers_past_their_last_year_lapse_and_their_ids_are_answered(self):
        offers = [{"id": "a#1", "expires": 100}, {"id": "b#1", "expires": 110}]
        self.assertEqual(figures.drop_lapsed_offers(offers, 105), ([{"id": "b#1", "expires": 110}], ["a#1"]))
        self.assertEqual(figures.drop_lapsed_offers(offers, 100), (offers, []))


if __name__ == "__main__":
    unittest.main()

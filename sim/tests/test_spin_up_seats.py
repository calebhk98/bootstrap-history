"""Places to learn a trade and the hidden spin-up: the search rules leave them to the masters and the schools, the
clearing rules open a place in every trade to every working person of an area while the economy settles."""

QUICK_TOPIC = True

import unittest

from sim.economy import rule_sets, spin_up_seats
from sim.labour.api import School


class ByMasters(unittest.TestCase):
    def test_the_years_schools_and_nothing_more_in_a_hidden_year(self):
        school = School("guild", "smith", "north", 12.0)
        self.assertEqual(spin_up_seats.by_masters([school], True, {"north": 500.0}, [("smith", "north"), ("potter", "north")]), (school,))


class OpenWhileSettling(unittest.TestCase):
    def test_a_year_of_play_has_the_years_schools_only(self):
        school = School("guild", "smith", "north", 12.0)
        self.assertEqual(spin_up_seats.open_while_settling([school], False, {"north": 500.0}, [("smith", "north")]), (school,))

    def test_a_hidden_year_adds_a_seat_for_each_working_person_of_the_area_in_every_trade_with_a_market_there(self):
        school = School("guild", "smith", "north", 12.0)
        markets = [("smith", "north"), ("potter", "north"), ("smith", "south")]
        seats = spin_up_seats.open_while_settling([school], True, {"north": 500.0, "south": 80.0}, markets)
        self.assertEqual(seats[0], school)
        added = {(seat.area, seat.trade): seat.seats for seat in seats[1:]}
        self.assertEqual(added, {("north", "potter"): 500.0, ("north", "smith"): 500.0, ("south", "smith"): 80.0})
        self.assertTrue(all(seat.completion_bonus == 0.0 for seat in seats[1:]))

    def test_an_area_with_no_working_people_gets_no_seat(self):
        self.assertEqual(spin_up_seats.open_while_settling([], True, {"north": 0.0}, [("smith", "north"), ("smith", "west")]), ())

    def test_the_seats_come_in_one_order_whatever_order_the_markets_are_given_in_and_a_market_named_twice_counts_once(self):
        one = spin_up_seats.open_while_settling([], True, {"north": 5.0, "south": 8.0}, [("smith", "north"), ("potter", "south")])
        other = spin_up_seats.open_while_settling([], True, {"south": 8.0, "north": 5.0}, [("potter", "south"), ("smith", "north"), ("smith", "north")])
        self.assertEqual(one, other)
        self.assertEqual(len(one), 2)


class MarketsOf(unittest.TestCase):
    def test_the_trade_and_the_area_of_each_labour_market_key(self):
        self.assertEqual(spin_up_seats.markets_of(["smith|north", "potter|far|south"], "|"), (("smith", "north"), ("potter", "far|south")))

    def test_a_key_without_the_separator_names_no_market(self):
        self.assertEqual(spin_up_seats.markets_of(["smith"], "|"), ())


class WorkingPeopleByArea(unittest.TestCase):
    def test_the_working_people_of_each_area_summed_over_its_households(self):
        households = [("north", 30.0), ("south", 8.0), ("north", 12.5)]
        self.assertEqual(spin_up_seats.working_people_by_area(households), {"north": 42.5, "south": 8.0})


class Rules(unittest.TestCase):
    def test_which_rule_each_set_runs(self):
        self.assertIs(rule_sets.RULE_SETS["search"].spin_up_seats, spin_up_seats.by_masters)
        self.assertIs(rule_sets.RULE_SETS["clearing"].spin_up_seats, spin_up_seats.open_while_settling)


if __name__ == "__main__":
    unittest.main()

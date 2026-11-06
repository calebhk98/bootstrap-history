"""markets/port_year_inputs.credit_line_asked: the line a seat asks the lenders for, in the economy's money."""
QUICK_TOPIC = True

import unittest

from sim.markets.port_year_inputs import credit_line_asked


class CreditLineAsked(unittest.TestCase):
    def test_the_line_is_held_to_what_the_seat_can_service(self):
        self.assertEqual(credit_line_asked(base=100.0, floor=0.0, serviceable=40.0, price_index=2.0, coin=4.0), 20.0)

    def test_the_running_cost_floor_lifts_a_line_the_seat_could_not_service(self):
        self.assertEqual(credit_line_asked(base=100.0, floor=60.0, serviceable=40.0, price_index=2.0, coin=4.0), 30.0)

    def test_a_seat_with_no_line_and_no_floor_asks_for_nothing(self):
        self.assertEqual(credit_line_asked(base=-5.0, floor=0.0, serviceable=-5.0, price_index=2.0, coin=4.0), 0.0)

    def test_the_base_under_serviceable_is_asked_whole(self):
        self.assertEqual(credit_line_asked(base=30.0, floor=10.0, serviceable=80.0, price_index=1.0, coin=2.0), 15.0)


if __name__ == "__main__":
    unittest.main()

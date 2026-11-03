"""The floor of the credit line (Complaint 665): the line the seat asks for never falls below the running costs, and lenders lend
it like any other line: where they grant less the seat has less. (The opening purse's repricing is tested in test_markets_reprice_opening_money.)"""

QUICK_TOPIC = True

import unittest

from sim.finance.rules import calculate_credit_ceiling


class CreditFloorTests(unittest.TestCase):
    def test_lenders_holding_nothing_leave_the_seat_no_line_not_a_floor_with_no_lender_behind_it(self):
        line = calculate_credit_ceiling(raw_credit=2000.0, running_cost_floor=107.0, serviceable=750.0, market_cap=0.0)
        self.assertEqual(line, 0.0)

    def test_lenders_granting_the_floor_lend_it_when_the_name_and_income_carry_less(self):
        self.assertEqual(calculate_credit_ceiling(50.0, 107.0, 80.0, market_cap=107.0), 107.0)
        self.assertEqual(calculate_credit_ceiling(50.0, 107.0, 80.0), 107.0)

    def test_lenders_with_room_raise_the_line_to_the_least_of_name_income_and_room(self):
        self.assertEqual(calculate_credit_ceiling(2000.0, 107.0, 750.0, market_cap=500.0), 500.0)
        self.assertEqual(calculate_credit_ceiling(2000.0, 107.0, 750.0, market_cap=5000.0), 750.0)


if __name__ == "__main__":
    unittest.main()

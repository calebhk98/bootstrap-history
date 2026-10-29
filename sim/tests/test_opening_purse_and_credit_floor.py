"""The floor of the credit line (Complaint 665): it never falls below the running costs, however little lenders hold beyond what
others owe. (The opening purse's repricing is tested in test_markets_reprice_opening_money.)"""

QUICK_TOPIC = True

import unittest

from sim.finance.rules import calculate_credit_ceiling


class CreditFloorTests(unittest.TestCase):
    def test_lenders_holding_nothing_leave_the_line_at_the_running_costs_not_at_the_name_or_the_income(self):
        floor = 107.0
        line = calculate_credit_ceiling(raw_credit=2000.0, running_cost_floor=floor, serviceable=750.0, market_cap=0.0)
        self.assertEqual(line, floor)

    def test_lenders_with_room_raise_the_line_to_the_least_of_name_income_and_room(self):
        self.assertEqual(calculate_credit_ceiling(2000.0, 107.0, 750.0, market_cap=500.0), 500.0)
        self.assertEqual(calculate_credit_ceiling(2000.0, 107.0, 750.0, market_cap=5000.0), 750.0)


if __name__ == "__main__":
    unittest.main()

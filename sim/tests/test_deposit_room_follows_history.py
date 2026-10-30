"""Complaint 519: a deposit's room a year is not below the rate the data say it was worked at (the same rate
`mined_before` draws it down by), so a district is not held to a fraction of what it historically raised; and
the ore a site allows is counted by the tonne of rock (a deposit stating no grade takes the expected one), not
as pure metal."""
QUICK_TOPIC = True

import unittest

from sim.resources.deposit_history import historical_rates
from sim.geography import api as geography
from sim.tests.test_mine_names_a_deposit import _Host


class DepositRoomTests(unittest.TestCase):

    def test_room_is_at_least_the_historical_rate_while_the_deposit_holds_that_much(self):
        host = _Host()
        checked = 0
        for resource_id in ("iron", "copper", "tin", "lead", "silver", "gold", "mercury"):
            rates = historical_rates(host.module.needs.deposit_catalogue()["metals"], resource_id)
            for row in host.found_deposits(resource_id):
                if row["id"] in rates:
                    checked += 1
                    self.assertGreaterEqual(row["rate_tonnes_per_year"] + 1e-9,
                                            min(rates[row["id"]], row["remaining_tonnes"]), row["id"])
        self.assertGreater(checked, 5)

    def test_every_metal_deposit_counts_its_ore_by_the_tonne_of_rock_not_of_metal(self):
        host = _Host()
        for resource_id in ("iron", "copper", "tin", "lead", "silver", "gold", "mercury"):
            for row in host.found_deposits(resource_id):
                self.assertTrue(row["grade_kg_per_tonne"], row["id"])
                self.assertGreater(geography.ore_tonnes_per_tonne(row), 1.0, row["id"])


if __name__ == "__main__":
    unittest.main()

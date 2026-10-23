"""reserve_staff (Complaint 176) is off by default for a player and for the optimizer. `default_policy` called once per mode.
The reserve rule is test_reserve_staff_policy; what is saved is test_state_save_fixed_point."""
import unittest

from sim.engine.seat_defaults import default_policy

QUICK_TOPIC = True


class DefaultPolicy(unittest.TestCase):

    def test_reserve_staff_is_listed_and_off_for_a_player(self):
        self.assertIs(default_policy(True)["reserve_staff"], False)

    def test_reserve_staff_is_listed_and_off_for_the_optimizer(self):
        self.assertIs(default_policy(False)["reserve_staff"], False)


if __name__ == "__main__":
    unittest.main()

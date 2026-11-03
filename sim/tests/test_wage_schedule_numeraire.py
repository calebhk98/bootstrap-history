"""build_schedule states the solve against the registry it is given: its unskilled trade, not the committed catalogue's."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.workforce import wage_schedule


class Stop(Exception):
    pass


class NumeraireOfTheRegistry(unittest.TestCase):
    def test_the_solve_is_asked_in_the_hour_of_the_registrys_unskilled_trade(self):
        registry = {"digger": {"family": "earth", "training_years": 0, "unskilled": True},
                    "smith": {"family": "metal", "training_years": 4}}
        civ = {"id": "x", "starting_techs": []}
        with mock.patch.object(wage_schedule.wage_provider, "coin_standard", return_value={"material": "silver", "kg_per_unit": 0.01}):
            with mock.patch.object(wage_schedule.wage_provider, "training_years_by_trade", return_value={"digger": 0.0, "smith": 4.0}):
                with mock.patch.object(wage_schedule.price_solver, "solved_prices", side_effect=Stop) as solve:
                    with self.assertRaises(Stop):
                        wage_schedule.build_schedule(registry, civ)
        self.assertEqual(solve.call_args.kwargs["unskilled_trade"], "digger")


if __name__ == "__main__":
    unittest.main()

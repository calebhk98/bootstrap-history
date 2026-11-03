"""Scholar hands count commissioned hours of the scholar trade only, the rule the pools' recount uses; the unskilled hour is
the wage the economy pays at the base tile."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour import trade_data
from sim.labour.labour_hands import Hands
from sim.labour.labour_wage_schedule import WageScheduleReader

YEAR_HOURS = 100.0


class ScholarHands(unittest.TestCase):
    def _hands(self, contract_hours):
        workforce = types.SimpleNamespace(scholars=2.0, contract_hours=contract_hours, hours_wanted_once={})
        world = types.SimpleNamespace(
            workforce=workforce, standing=types.SimpleNamespace(founder_alive=False),
            economy=types.SimpleNamespace(agent_working_hours=lambda: YEAR_HOURS),
            trades=types.SimpleNamespace(trade_family=lambda trade: "learned", HOURS_PER_PERSON_YEAR=YEAR_HOURS))
        return Hands(world, supply=None, trades=None)

    def test_hours_of_another_trade_in_the_scholar_family_do_not_make_a_scholar(self):
        hands = self._hands({"merchant": 300.0})
        self.assertEqual(hands.scholar_hands_available(), 2.0)

    def test_hours_of_the_scholar_trade_do(self):
        hands = self._hands({trade_data.scholar_trade(): 300.0, "merchant": 300.0})
        self.assertEqual(hands.scholar_hands_available(), 5.0)


class UnskilledHour(unittest.TestCase):
    def test_the_hour_is_read_at_the_base_tile_for_the_unskilled_trade(self):
        asked = []
        opening = types.SimpleNamespace(training_years={"digger": 0.0, "smith": 4.0}, money_per_labour_hour=1.0,
                                        priced_at=lambda paid: ("priced", paid))
        world = types.SimpleNamespace(
            trades=types.SimpleNamespace(trade_registry={"digger": {"family": "earth", "training_years": 0.0}, "smith": {"family": "metal", "training_years": 4.0}}, trade_family=lambda trade: "x",
                                         build_wage_schedule=lambda civ: opening),
            scenario=types.SimpleNamespace(civ=None),
            economy=types.SimpleNamespace(agent_wage_at=lambda trade, tile: asked.append((trade, tile)) or 3.5),
            finance=types.SimpleNamespace(home_price_level=lambda: 1.0))
        reader = WageScheduleReader(world, types.SimpleNamespace(base_tile=lambda: "home"))
        self.assertEqual(reader.wage_schedule(), ("priced", 3.5))
        self.assertEqual(asked, [("digger", "home")])


class WorkforceReport(unittest.TestCase):
    def test_people_in_training_are_counted_by_the_people_in_the_rows(self):
        from sim.labour.labour_staff_ledger import StaffLedger
        from sim.workforce.api import TrainingRow
        workforce = types.SimpleNamespace(training=[TrainingRow("smith", 3.0, 104.0), TrainingRow(None, 2.5, 105.0)],
                                          reserve_craftsmen=0, reserve_scholars=0)
        world = types.SimpleNamespace(workforce=workforce, game=types.SimpleNamespace(policy={}))
        ledger = StaffLedger(world, book=types.SimpleNamespace(employed_total=lambda: 0.0), market=None)
        ledger.sole_supervisors = lambda: []
        self.assertEqual(ledger.workforce_report()["in_training"], 5.5)


class SchoolRecords(unittest.TestCase):
    def test_each_trade_with_seats_is_a_school_in_the_area_and_empty_ones_are_not(self):
        from sim.labour.api import School, schools_of_actor
        schools = schools_of_actor("founder", "area_a", {"smith": 3, "carter": 0, "baker": 2.0})
        self.assertEqual(schools, (School("founder", "baker", "area_a", 2.0), School("founder", "smith", "area_a", 3.0)))


class TradeSchool(unittest.TestCase):
    def test_no_seats_is_refused_as_such_and_not_as_unaffordable(self):
        from sim.labour.labour_training import Training
        world = types.SimpleNamespace(trades=types.SimpleNamespace(wages={"smith": 1.0}))
        training = Training(world, advice=None, book=None, capacity=None, hours=None, market=None, supply=None,
                            trades=types.SimpleNamespace(trade_available=lambda trade: True))
        done, reason = training.found_trade_school("smith", 0)
        self.assertFalse(done)
        self.assertNotIn("afford", reason)   # presentation: the refusal names the real cause


if __name__ == "__main__":
    unittest.main()

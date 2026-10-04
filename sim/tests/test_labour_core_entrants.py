"""Entrants choose a trade by lifetime value and ability, within the places that exist."""
import unittest

from sim.labour.market import aptitude, entrants, trades
from sim.labour.market.records import Clearing, MarketState, School, YearInputs, YearReport

AREA = "plain"
HOURS = 1000.0
SUBSISTENCE = 500.0


def _specs(**overrides):
    registry = {
        "digger": {"family": "earth", "training_years": 0, "difficulty": -3.0, "fallback": True},
        "carver": {"family": "craft", "training_years": 2, "difficulty": 0.0},
        "healer": {"family": "care", "training_years": 6, "difficulty": 1.0},
    }
    for trade, changes in overrides.items():
        registry[trade] = dict(registry.get(trade, {}), **changes)
    return trades.trade_specs(registry)


def _clearings(wages):
    result = {}
    for trade, wage in wages.items():
        result[(AREA, trade)] = Clearing(
            trade=trade, area=AREA, wage=wage, hours_offered=HOURS, hours_wanted=HOURS, hours_hired=HOURS,
            hired_by_employer={}, paid_by_employer={}, average_wage=wage)
    return result


def _inputs(specs, entrant_count=100.0, seats=1000.0, **kwargs):
    schools = [School("school", trade, AREA, seats) for trade in specs
               if specs[trade].training_years > 0.0] if seats else []
    return YearInputs(
        trades=specs, bids=[], subsistence_per_worker_year={AREA: SUBSISTENCE}, hours_per_worker_year=HOURS,
        discount_rate=0.03, career_years=40.0, entrants={AREA: entrant_count}, schools=schools, **kwargs)


def _run(inputs, wages, state=None):
    state = state or MarketState()
    report = YearReport()
    entrants.place_entrants(state, inputs, _clearings(wages), report)
    return state, report


def _everyone(state):
    total = 0.0
    for by_trade in state.workers.values():
        total += sum(sum(bands) for bands in by_trade.values())
    for by_trade in state.trainees.values():
        for cohorts in by_trade.values():
            total += sum(sum(cohort[1]) for cohort in cohorts)
    return total


class EntrantTests(unittest.TestCase):

    def test_higher_paying_trade_draws_more_entrants(self):
        specs = _specs()
        _, low = _run(_inputs(specs), {"digger": 0.5, "carver": 0.6, "healer": 0.5})
        _, high = _run(_inputs(specs), {"digger": 0.5, "carver": 1.0, "healer": 0.5})
        self.assertGreater(high.entered[AREA]["carver"], low.entered[AREA]["carver"])

    def test_hard_trade_draws_from_top_bands(self):
        state, _ = _run(_inputs(_specs()), {"digger": 0.5, "carver": 0.6, "healer": 1.5})
        healers = [0.0] * aptitude.band_count()
        for cohort in state.trainees[AREA]["healer"]:
            aptitude.add_bands(healers, cohort[1])
        self.assertGreater(healers[-1], 3.0 * healers[0])

    def test_long_training_needs_higher_wage_for_same_entrants(self):
        specs = _specs(carver={"difficulty": 0.0, "training_years": 2},
                       healer={"difficulty": 0.0, "training_years": 8})
        _, equal = _run(_inputs(specs), {"digger": 0.5, "carver": 1.0, "healer": 1.0})
        self.assertLess(equal.entered[AREA]["healer"], equal.entered[AREA]["carver"])
        _, higher = _run(_inputs(specs), {"digger": 0.5, "carver": 1.0, "healer": 3.0})
        self.assertGreater(higher.entered[AREA]["healer"], higher.entered[AREA]["carver"])

    def test_capacity_limited_trade_overflows_to_other_choices(self):
        specs = _specs()
        inputs = _inputs(specs, seats=0.0)
        inputs.schools = [School("school", "carver", AREA, 5.0), School("school", "healer", AREA, 1000.0)]
        state, report = _run(inputs, {"digger": 0.5, "carver": 3.0, "healer": 0.6})
        self.assertAlmostEqual(report.entered[AREA]["carver"], 5.0)
        self.assertAlmostEqual(sum(report.entered[AREA].values()), 100.0)
        self.assertAlmostEqual(_everyone(state), 100.0)

    def test_nowhere_to_learn_means_no_trainees(self):
        specs = _specs()
        state, report = _run(_inputs(specs, seats=0.0), {"digger": 0.5, "carver": 3.0, "healer": 3.0})
        self.assertNotIn("carver", state.trainees.get(AREA, {}))
        self.assertNotIn("healer", state.trainees.get(AREA, {}))
        self.assertAlmostEqual(report.entered[AREA]["digger"], 100.0)
        self.assertAlmostEqual(sum(state.workers[AREA]["digger"]), 100.0)

    def test_people_are_conserved_with_existing_state(self):
        specs = _specs()
        state = MarketState(workers={AREA: {"carver": [10.0] * aptitude.band_count()}})
        before = _everyone(state)
        state, report = _run(_inputs(specs, entrant_count=237.0, seats=3.0),
                             {"digger": 0.5, "carver": 1.2, "healer": 1.5}, state)
        self.assertAlmostEqual(_everyone(state), before + 237.0)
        self.assertAlmostEqual(sum(report.entered[AREA].values()), 237.0)

    def test_enterable_set_limits_choice(self):
        specs = _specs()
        inputs = _inputs(specs, enterable_trades=frozenset({"digger", "carver"}))
        state, report = _run(inputs, {"digger": 0.5, "carver": 1.0, "healer": 9.0})
        self.assertNotIn("healer", report.entered[AREA])
        self.assertAlmostEqual(_everyone(state), 100.0)


if __name__ == "__main__":
    unittest.main()

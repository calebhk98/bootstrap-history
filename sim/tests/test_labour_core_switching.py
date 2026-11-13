"""Workers switch trades when the gain beats retraining, and become trainees of the new trade."""

QUICK_TOPIC = True

import copy
import unittest

from sim.labour.market import aptitude, switching, trades
from sim.labour.market.records import LabourClearing, MarketState, School, YearInputs, YearReport

AREA = "plain"
HOURS = 1000.0
SUBSISTENCE = 500.0


def _specs():
    return trades.trade_specs({
        "digger": {"family": "earth", "training_years": 0, "difficulty": -3.0, "fallback": True},
        "carver": {"family": "craft", "training_years": 4, "difficulty": 0.0},
        "cutter": {"family": "craft", "training_years": 4, "difficulty": 0.0},
        "healer": {"family": "care", "training_years": 4, "difficulty": 0.0},
    })


def _clearings(wages):
    return {(AREA, trade): LabourClearing(
        trade=trade, area=AREA, wage=wage, hours_offered=HOURS, hours_wanted=HOURS, hours_hired=HOURS,
        hired_by_employer={}) for trade, wage in wages.items()}


def _inputs(specs):
    schools = [School("school", trade, AREA, 1000.0) for trade, spec in specs.items() if spec.training_years > 0]
    return YearInputs(
        trades=specs, bids=[], subsistence_per_worker_year={AREA: SUBSISTENCE}, hours_per_worker_year=HOURS,
        discount_rate=0.03, career_years=40.0, schools=schools)


def _state(counts):
    bands = aptitude.band_count()
    return MarketState(workers={AREA: {trade: [count / bands] * bands for trade, count in counts.items()}})


def _everyone(state):
    total = sum(sum(bands) for by_trade in state.workers.values() for bands in by_trade.values())
    for by_trade in state.trainees.values():
        for cohorts in by_trade.values():
            total += sum(sum(cohort[1]) for cohort in cohorts)
    return total


def _run(counts, wages):
    state = _state(counts)
    report = YearReport()
    switching.switch_trades(state, _inputs(_specs()), _clearings(wages), report)
    return state, report


def _trainees(state, trade):
    return sum(sum(cohort[1]) for cohort in state.trainees.get(AREA, {}).get(trade, []))


class SwitchingTests(unittest.TestCase):

    def test_no_wage_gap_means_no_switching(self):
        state, report = _run({"digger": 1000.0, "carver": 1000.0},
                             {"digger": 0.5, "carver": 0.5, "cutter": 0.5, "healer": 0.5})
        # every destination is weighed with staying, so a few who must pay for training still try an equal trade; they are few
        trainees = sum(_trainees(state, trade) for trade in ("carver", "cutter", "healer"))
        self.assertLess(trainees, 0.01 * 2000.0)
        self.assertAlmostEqual(sum(report.switched.get(AREA, {}).values()), 0.0)

    def test_bigger_gap_means_more_switching(self):
        wages = {"digger": 0.5, "cutter": 0.5, "healer": 0.5}
        _, small = _run({"digger": 1000.0, "carver": 1000.0}, dict(wages, carver=0.8))
        _, large = _run({"digger": 1000.0, "carver": 1000.0}, dict(wages, carver=2.5))
        self.assertGreater(large.switched[AREA]["carver"], small.switched[AREA]["carver"])
        self.assertLess(large.switched[AREA]["carver"],
                        1000.0 * switching.SWITCHING_CONSIDERATION_SHARE_PER_YEAR + 1e-9)

    def test_those_who_sold_no_hours_consider_a_switch_more_than_those_who_did(self):
        wages = {"digger": 0.5, "carver": 2.5, "cutter": 0.5, "healer": 0.5}
        _, working = _run({"digger": 1000.0}, wages)
        idle_clearings = _clearings(wages)
        idle_clearings[(AREA, "digger")] = LabourClearing(
            trade="digger", area=AREA, wage=0.5, hours_offered=HOURS, hours_wanted=0.0, hours_hired=0.0,
            hired_by_employer={})
        state = _state({"digger": 1000.0})
        report = YearReport()
        switching.switch_trades(state, _inputs(_specs()), idle_clearings, report)
        self.assertGreater(report.switched[AREA]["carver"], working.switched[AREA]["carver"])

    def test_switchers_become_trainees_not_workers(self):
        state, report = _run({"digger": 1000.0}, {"digger": 0.5, "carver": 2.0, "cutter": 0.5, "healer": 0.5})
        self.assertAlmostEqual(_trainees(state, "carver"), report.switched[AREA]["carver"])
        self.assertAlmostEqual(sum(state.workers[AREA].get("carver", [0.0])), 0.0)
        others = sum(count for trade, count in report.switched[AREA].items() if trade != "digger")
        self.assertAlmostEqual(report.switched[AREA]["digger"], -others)

    def test_same_family_retrains_faster(self):
        state, _ = _run({"carver": 1000.0}, {"carver": 0.5, "cutter": 2.0, "healer": 2.0, "digger": 0.5})
        years = {trade: state.trainees[AREA][trade][0][0] for trade in ("cutter", "healer")}
        self.assertAlmostEqual(years["cutter"], 4.0 * switching.RETRAINING_SHARE_WITHIN_FAMILY)
        self.assertAlmostEqual(years["healer"], 4.0)
        self.assertGreater(_trainees(state, "cutter"), _trainees(state, "healer"))

    def test_people_are_conserved_when_places_run_out(self):
        specs = _specs()
        inputs = _inputs(specs)
        inputs.schools = [School("school", "carver", AREA, 2.0)]
        state = _state({"digger": 1000.0, "healer": 300.0})
        report = YearReport()
        switching.switch_trades(state, inputs, _clearings(
            {"digger": 0.5, "carver": 2.5, "cutter": 0.5, "healer": 0.6}), report)
        self.assertAlmostEqual(_everyone(state), 1300.0)
        self.assertLessEqual(_trainees(state, "carver"), 2.0 + 1e-9)
        self.assertAlmostEqual(sum(report.switched[AREA].values()), 0.0)

    def test_same_inputs_same_result(self):
        wages = {"digger": 0.5, "carver": 1.5, "cutter": 1.2, "healer": 1.0}
        first, _ = _run({"digger": 800.0, "healer": 200.0}, wages)
        second, _ = _run({"digger": 800.0, "healer": 200.0}, wages)
        self.assertEqual(first.trainees, second.trainees)
        self.assertEqual(first.workers, copy.deepcopy(second.workers))



class PipelineTests(unittest.TestCase):
    """A trade that already has incumbents is weighed by what it will pay once a switcher is trained,
    the same as one nobody practises: a shortage the people already training will fill draws nobody."""

    def _carver_shortage(self, trainees):
        state = _state({"digger": 1000.0, "carver": 100.0})
        if trainees:
            bands = aptitude.band_count()
            state.trainees = {AREA: {"carver": [[3.0, [trainees / bands] * bands, 0.0]]}}
        clearings = _clearings({"digger": 0.5, "cutter": 0.5, "healer": 0.5})
        clearings[(AREA, "carver")] = LabourClearing(
            trade="carver", area=AREA, wage=2.0, hours_offered=100.0 * HOURS, hours_wanted=300.0 * HOURS,
            hours_hired=100.0 * HOURS, hired_by_employer={})
        report = YearReport()
        switching.switch_trades(state, _inputs(_specs()), clearings, report)
        return report.switched.get(AREA, {}).get("carver", 0.0)

    def test_an_unfilled_shortage_draws_switchers(self):
        self.assertGreater(self._carver_shortage(trainees=0.0), 0.0)

    def test_a_shortage_the_trainees_will_fill_draws_nobody(self):
        # a shortage already being filled draws only the few every destination draws; far fewer than an unfilled one
        self.assertLess(self._carver_shortage(trainees=800.0), 0.1 * self._carver_shortage(trainees=0.0))


class FrictionalVacancyTests(unittest.TestCase):
    def _switched(self, hired):
        state = _state({"digger": 1000.0, "carver": 400.0})
        clearings = _clearings({"digger": 0.5, "cutter": 0.5, "healer": 0.5})
        clearings[(AREA, "carver")] = LabourClearing(
            trade="carver", area=AREA, wage=1.0, hours_offered=400.0 * HOURS, hours_wanted=200.0 * HOURS,
            hours_hired=hired * HOURS, hired_by_employer={})
        report = YearReport()
        switching.switch_trades(state, _inputs(_specs()), clearings, report)
        return report.switched.get(AREA, {}).get("carver", 0.0)

    def test_a_few_unfilled_hours_in_a_glutted_trade_do_not_make_it_a_sure_job(self):
        self.assertAlmostEqual(self._switched(hired=199.0), self._switched(hired=200.0), delta=0.05 * self._switched(hired=200.0))


class NoWorthlessSwitchTests(unittest.TestCase):
    def test_a_trade_paying_a_hair_more_draws_what_a_hair_less_draws(self):
        # no threshold at the unskilled wage: the training cost already prices an unattractive trade, and the draw is continuous
        floor_wage = SUBSISTENCE / HOURS
        more, _ = _run({"digger": 1000.0}, {"digger": floor_wage, "carver": floor_wage * (1.0 + 1e-12)})
        less, _ = _run({"digger": 1000.0}, {"digger": floor_wage, "carver": floor_wage * (1.0 - 1e-12)})
        self.assertAlmostEqual(_trainees(more, "carver"), _trainees(less, "carver"), places=6)


if __name__ == "__main__":
    unittest.main()

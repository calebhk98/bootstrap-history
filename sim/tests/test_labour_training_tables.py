"""`training.advance` over the trainees table gives what the rule written out on dicts gave: ages, graduates, falls back, and keeps the
order of the views."""

QUICK_TOPIC = True

import random
import unittest

from sim.labour.market import aptitude, records, trades, training
from sim.labour.market.records import MarketState, YearReport

REGISTRY = {"digger": {"family": "toil", "training_years": 0}, "carver": {"family": "craft", "training_years": 3},
            "healer": {"family": "lore", "training_years": 6, "difficulty": 1.0}}


def reference_advance(plain, specs, fallback):
    """The rule as it was written on nested dicts: returns (workers, trainees, graduated)."""
    workers = {area: {trade: list(bands) for trade, bands in by_trade.items()} for area, by_trade in plain["workers"].items()}
    trainees = {area: {trade: [[c[0], list(c[1]), c[2]] for c in cohorts] for trade, cohorts in by_trade.items()}
                for area, by_trade in plain["trainees"].items()}
    graduated = {}
    for area in sorted(trainees):
        by_trade = trainees[area]
        for trade in sorted(by_trade):
            still = []
            spec = specs.get(trade)
            for years_left, bands, bonus in by_trade[trade]:
                years_left -= 1.0
                if years_left > training.GRADUATION_TOLERANCE_YEARS:
                    still.append([years_left, bands, bonus])
                    continue
                chances = aptitude.completion_by_band(spec.difficulty, bonus) if spec is not None else aptitude.empty_bands()
                finished = [value * chance for value, chance in zip(bands, chances)]
                failed = [value - done for value, done in zip(bands, finished)]
                held = workers.setdefault(area, {})
                aptitude.add_bands(aptitude.bands_of(held, trade), finished)
                aptitude.add_bands(aptitude.bands_of(held, fallback), failed)
                graduated.setdefault(area, {})[trade] = graduated.get(area, {}).get(trade, 0.0) + aptitude.band_total(finished)
            if still:
                by_trade[trade] = still
            else:
                del by_trade[trade]
        if not by_trade:
            del trainees[area]
    return workers, trainees, graduated


class AdvanceMatchesTheDictRule(unittest.TestCase):
    def test_random_states(self):
        rng = random.Random(4)
        specs = trades.trade_specs(REGISTRY)
        inputs = records.YearInputs(trades=specs, bids=[], subsistence_per_worker_year={}, hours_per_worker_year=2000.0,
                                    discount_rate=0.05, career_years=30.0)
        bands = aptitude.band_count()
        for _case in range(60):
            names = ["a%d" % each for each in range(rng.randint(1, 4))]
            workers = {area: {trade: [rng.uniform(0, 30) for _ in range(bands)] for trade in rng.sample(["digger", "carver", "healer"], rng.randint(0, 3))}
                       for area in names}
            trainees = {area: {trade: [[float(rng.randint(1, 3)), [rng.uniform(0, 9) for _ in range(bands)], rng.choice([0.0, 0.4])]
                                       for _ in range(rng.randint(1, 3))]
                               for trade in rng.sample(["carver", "healer", "unlisted"], rng.randint(1, 3))} for area in names if rng.random() < 0.8}
            state = MarketState(workers=workers, trainees=trainees)
            want_workers, want_trainees, want_graduated = reference_advance(state.to_plain(), specs, "digger")
            report = YearReport()
            training.advance(state, inputs, report)
            got = state.to_plain()
            self.assertEqual(got["workers"], want_workers)
            self.assertEqual(got["trainees"], want_trainees)
            self.assertEqual(report.graduated, want_graduated)
            self.assertEqual(list(state.workers), list(want_workers), "areas keep the order they were named in")
            for area in want_workers:
                self.assertEqual(list(state.workers[area]), list(want_workers[area]), "pairs keep the order they were made in")


if __name__ == "__main__":
    unittest.main()

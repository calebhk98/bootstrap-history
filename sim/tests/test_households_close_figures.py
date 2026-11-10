"""The cohorts' scalar close figures in one kernel call against `households_close.closed_figures` cohort by cohort, on written-out and
seeded random inputs (under numba and ROME_NO_JIT=1). Floats agree to a relative 1e-12; the kernel does the Python's arithmetic in its order."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

import numpy as np

from sim.economy import households_close, households_close_figures

GRAIN = SimpleNamespace(needs=[SimpleNamespace(goods=[("grain", 1.0)])])
NOTHING = SimpleNamespace(needs=[])


class StubView:
    """A view with a price level and observed inflation per currency, and equity and claims per agent."""

    def __init__(self, observed, equity, claims):
        self.observed, self.equity_of, self.claims_of = observed, equity, claims

    def area_of(self, good, tile):
        return "area:" + tile

    def currency_of(self, area):
        return "gold" if area.endswith("a") else "silver"

    def basket_price_level(self, currency):
        return 1.25 if currency == "gold" else 0.8

    def observed_inflation(self, currency):
        return self.observed.get(currency)

    def equity(self, agent):
        return self.equity_of.get(agent, 0.0)

    def claims(self, agent, currency):
        return self.claims_of.get(agent, 0.0)


def plain(view, agent, tile, basket, values):
    return households_close.closed_figures(agent, tile, values["people"], values["expected_inflation"], values["last_basket_price_level"],
                                           values["cash_target"], values["share_wealth"], values["last_year_income"],
                                           values["expected_spending"], values["planned_spending"], values["expected_floor_cost"], {},
                                           view, basket, values["income"], values["spent"], values["floor_cost"], {})


def both(view, cohorts):
    """(kernel figures by field, the plain figures by cohort) for cohorts given as (agent, tile, basket, values)."""
    names = households_close_figures.FIELDS
    columns = {name: np.array([values[name] if values[name] is not None else np.nan for _a, _t, _b, values in cohorts]) for name in names}
    figures = households_close_figures.closed_scalars_of(
        view, [each[0] for each in cohorts], [each[1] for each in cohorts], [each[2] for each in cohorts], columns,
        np.array([each[3]["people"] for each in cohorts]), np.array([each[3]["income"] for each in cohorts]),
        np.array([each[3]["spent"] for each in cohorts]), np.array([each[3]["floor_cost"] for each in cohorts]))
    return figures, [plain(view, *each) for each in cohorts]


def values(rng):
    return {"people": rng.uniform(1, 300), "expected_inflation": rng.uniform(-0.1, 0.3), "last_basket_price_level": rng.uniform(0.5, 2.0),
            "cash_target": rng.uniform(0, 50), "share_wealth": rng.choice([None, 0.0, rng.uniform(0, 4000)]),
            "last_year_income": rng.choice([0.0, rng.uniform(1, 900)]), "expected_spending": rng.choice([0.0, rng.uniform(1, 900)]),
            "planned_spending": rng.choice([0.0, rng.uniform(1, 900)]), "expected_floor_cost": rng.choice([0.0, rng.uniform(1, 500)]),
            "income": rng.choice([0.0, rng.uniform(1, 900)]), "spent": rng.uniform(0, 900), "floor_cost": rng.uniform(0, 5)}


class ScalarFiguresEqualThePlainClose(unittest.TestCase):

    def check(self, view, cohorts):
        figures, expected = both(view, cohorts)
        for position, answer in enumerate(expected):
            for name in households_close_figures.FIELDS:
                want = answer[name]
                got = figures[name][position]
                if want is None:
                    self.assertTrue(np.isnan(got), (name, position))
                else:
                    self.assertAlmostEqual(got, want, delta=1e-12 * max(1.0, abs(want)), msg=(name, position))

    def test_a_written_out_cohort(self):
        view = StubView({"gold": 0.1}, {"c": 300.0}, {"c": 20.0})
        one = {"people": 100.0, "expected_inflation": 0.02, "last_basket_price_level": 1.0, "cash_target": 5.0, "share_wealth": None,
               "last_year_income": 80.0, "expected_spending": 70.0, "planned_spending": 90.0, "expected_floor_cost": 60.0, "income": 100.0,
               "spent": 85.0, "floor_cost": 0.5}
        self.check(view, [("c", "a", GRAIN, one)])
        figures, _expected = both(view, [("c", "a", GRAIN, one)])
        self.assertAlmostEqual(figures["expected_inflation"][0], 0.02 + 0.5 * (0.1 - 0.02))

    def test_a_basket_with_no_good_keeps_the_price_figures(self):
        view = StubView({}, {}, {})
        one = {"people": 10.0, "expected_inflation": 0.02, "last_basket_price_level": 1.0, "cash_target": 5.0, "share_wealth": 7.0,
               "last_year_income": 0.0, "expected_spending": 0.0, "planned_spending": 0.0, "expected_floor_cost": 0.0, "income": 4.0,
               "spent": 3.0, "floor_cost": 0.5}
        self.check(view, [("c", "a", NOTHING, one)])

    def test_random_cohorts(self):
        for seed in range(40):
            rng = random.Random(seed)
            view = StubView({"gold": rng.choice([None, 0.05, -0.2]), "silver": rng.choice([None, 0.3])},
                            {"c%d" % each: rng.choice([0.0, rng.uniform(0, 5000)]) for each in range(6)},
                            {"c%d" % each: rng.choice([0.0, rng.uniform(0, 900)]) for each in range(6)})
            cohorts = [("c%d" % each, rng.choice(["a", "b"]), rng.choice([GRAIN, GRAIN, NOTHING]), values(rng)) for each in range(6)]
            self.check(view, cohorts)


if __name__ == "__main__":
    unittest.main()

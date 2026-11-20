"""SMOKE: the hand-built three-tile economy with plant in its smelting, on the clearing rule set (Complaint 473). Its
watched quantities come to rest, its smelters end working about the share of their plant that pays the plant's charge
and not all of it, and with a tenth fewer people it ends with less plant. Whole economies are stepped for a century and
a half; the rules are tested one function at a time in test_capacity_by_working and test_plant_by_working.
The opening's wages and prices stand where this economy rests (the smelters' plant has to earn its charge out of a
metal the mint holds at a fixed price, so wages stand lower than in the plantless fixture)."""
import unittest

from sim.economy import api as economy_api
from sim.economy.api import RULE_SET_CLEARING
from sim.economy.fixture_setups import GRAIN, LABOURER, METAL, MINER, ORE, SMELT, SMITH, recipes, stationary_setup
from sim.economy.types import Recipe
from sim.markets.spin_up import SPIN_UP_TOLERANCE
from sim.tests.economy_fixture import quiet_year
from sim.tests.test_economy_rest_smoke import SHOCK_YEAR, fewer_people, yearly_moves

TOPIC_SECONDS = 600
YEARS = 150
RESTING_FROM = 110
WAGE_SCALE = 0.75                 # the opening's wages and other prices against the plantless fixture's
PLANT_ORE_PER_RUN = 400.0         # ore built into the plant that smelts one run a year
PLANT_LIFE_YEARS = 10.0
WATCHED = ("price_level", "wage", "hired_hours")


def plant_setup():
    smelt = Recipe(SMELT, {METAL: 1.0}, {ORE: 1000.0}, {SMITH: 30.0}, {ORE: PLANT_ORE_PER_RUN}, {}, PLANT_LIFE_YEARS)
    return stationary_setup(rule_set=RULE_SET_CLEARING, recipes={**recipes(), SMELT: smelt},
                            opening_prices={GRAIN: 0.3 * WAGE_SCALE, ORE: 0.05 * WAGE_SCALE, METAL: 95.0},
                            opening_wages={LABOURER: 1.0 * WAGE_SCALE, MINER: 1.2 * WAGE_SCALE, SMITH: 1.5 * WAGE_SCALE})


def stepped(inputs_for_year=None):
    """One row a year: the watched quantities, the smelters' plant in runs and the runs they worked."""
    setup = plant_setup()
    economy = economy_api.blank_economy(setup)
    rows = []
    for year in range(YEARS):
        outcome = economy.step(quiet_year(setup) if inputs_for_year is None else inputs_for_year(economy, year))
        smelters = [producer for producer in economy.record.producers.values() if producer.recipe_id == SMELT]
        rows.append({"price_level": outcome.basket_price_level, "wage": outcome.wages[LABOURER], "hired_hours": outcome.hired_hours,
                     "plant": sum(producer.capacity_runs for producer in smelters),
                     "worked": sum(max(producer.last_runs, 0.0) for producer in smelters)})
    return rows


def mean_plant(rows):
    """The smelters' plant averaged over the resting years."""
    resting = rows[RESTING_FROM:]
    return sum(row["plant"] for row in resting) / len(resting)


class ClearingRuleSetWithPlant(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = stepped()
        cls.fewer = stepped(fewer_people)

    def test_the_watched_quantities_rest(self):
        for name in WATCHED:
            self.assertLess(max(yearly_moves(self.base, name, RESTING_FROM)), SPIN_UP_TOLERANCE / 2.0, name)

    def test_the_smelters_end_working_a_part_of_their_plant_and_not_all_of_it(self):
        share = self.base[-1]["worked"] / self.base[-1]["plant"]
        self.assertGreater(share, 0.5)
        self.assertLess(share, 0.9)

    def test_the_plant_is_kept_up(self):
        self.assertGreater(self.base[-1]["plant"], 0.5 * self.base[0]["plant"])

    def test_a_tenth_fewer_people_end_with_less_plant(self):
        # over the resting years, not the last one: the plant itself swings by a few per cent with its own life
        self.assertEqual(self.fewer[SHOCK_YEAR - 1]["plant"], self.base[SHOCK_YEAR - 1]["plant"])
        self.assertLess(mean_plant(self.fewer), 0.95 * mean_plant(self.base))


if __name__ == "__main__":
    unittest.main()

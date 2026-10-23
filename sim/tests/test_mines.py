"""mines: depletion and the cost scale of a working (Complaint 640 audit: rules on a stub founder holding workings, no
game). The ceiling bound, the running cost, the quote and closing are test_mine_works_wiring; the ceiling
arithmetic is test_mine_ceiling_rules."""
import types

from .harness import *  # noqa: F401,F403
from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.engine.economy_mining import MiningMixin

QUICK_TOPIC = True


class _Founder(MiningMixin):
    """The part of a Sim that a working's depletion reads: a list of workings, the land ceiling and the year."""

    def __init__(self, ceiling=100.0, year=1):
        self.holdings = types.SimpleNamespace(mines=[], mine_tranches=[], mine_pending={})
        self.household = self.holdings
        self.state = types.SimpleNamespace(holdings=self.holdings, scenario=types.SimpleNamespace(year=year))
        self._ceiling = ceiling

    def mine_land_ceiling(self, mat):
        return self._ceiling

    def _draw_working(self, working):
        pass

    def add_working(self, material="coal", capacity=10.0, opened_year=1, intensity=0.0):
        working = {"material": material, "capacity": capacity, "opened_year": opened_year,
                   "capex_paid": 0.0, "intensity_yrs": intensity}
        self.holdings.mines.append(working)
        return working

    def pass_years(self, years):
        for _ in range(years):
            self.state.scenario.year += 1
            self.commission_mines()


# --- yield falls as a working is worked hard relative to what the ground can support, never below the floor.
hard = _Founder(ceiling=100.0)
hard_working = hard.add_working(capacity=90.0)
check("a new working yields its whole rated capacity", hard.mine_yield_t_for(hard_working) == 90.0,
      hard.mine_yield_t_for(hard_working))
hard.pass_years(int(hard.DEPLETION_HALF_LIFE_YRS))
check("a working driven hard for the half-life years yields less than it did when it opened",
      hard.mine_yield_t_for(hard_working) < 90.0, hard.mine_yield_t_for(hard_working))
check("...and its depletion factor is the share of day one still left",
      abs(hard.mine_depletion_factor_for(hard_working)
          - max(hard.DEPLETION_FLOOR, 1.0 - hard_working["intensity_yrs"] / hard.DEPLETION_HALF_LIFE_YRS)) < 1e-12, None)
hard.pass_years(2000)
check("...and depletion saturates at the floor rather than falling without limit",
      abs(hard.mine_depletion_factor_for(hard_working) - hard.DEPLETION_FLOOR) < 1e-12,
      hard.mine_depletion_factor_for(hard_working))
check("a working below the floor never yields less than the floor share of its capacity",
      hard.mine_yield_t_for(hard_working) >= hard.DEPLETION_FLOOR * 90.0 - 1e-9, hard.mine_yield_t_for(hard_working))

# --- a working driven gently depletes slower than one driven hard, for the same years.
gentle = _Founder(ceiling=100.0)
gentle_working = gentle.add_working(capacity=10.0)
hard_again = _Founder(ceiling=100.0)
hard_again_working = hard_again.add_working(capacity=90.0)
gentle.pass_years(20)
hard_again.pass_years(20)
check("a working driven at a tenth of what the land could support depletes slower than one driven at nine tenths",
      gentle.mine_depletion_factor_for(gentle_working) > hard_again.mine_depletion_factor_for(hard_again_working),
      (gentle.mine_depletion_factor_for(gentle_working), hard_again.mine_depletion_factor_for(hard_again_working)))
check("a year adds the working's capacity over the ceiling to its intensity",
      abs(gentle_working["intensity_yrs"] - 20 * 10.0 / 100.0) < 1e-9, gentle_working["intensity_yrs"])

# --- a working is a thing: two workings of one material keep their own clocks.
two = _Founder(ceiling=100.0)
older = two.add_working(capacity=40.0, opened_year=1)
two.holdings.mine_tranches = [("coal", 20.0, 51)]
two.pass_years(50)
newer = two.holdings.mines[1]
two.pass_years(50)
check("a tranche that comes on stream later becomes its own working, not merged into the older one",
      len(two.holdings.mines) == 2 and newer["opened_year"] == 51 and older["opened_year"] == 1,
      [(working["opened_year"], working["capacity"]) for working in two.holdings.mines])
check("the newer working is less worked-out than the older, having aged from its own commissioning year",
      two.mine_depletion_factor_for(newer) > two.mine_depletion_factor_for(older),
      (two.mine_depletion_factor_for(older), two.mine_depletion_factor_for(newer)))
check("the material's yield is the sum of each working's own actual output",
      abs(two.mine_yield_t("coal") - sum(two.mine_yield_t_for(working) for working in two.holdings.mines)) < 1e-9,
      two.mine_yield_t("coal"))
check("the material's depletion is the capacity-weighted average of its workings'",
      abs(two.mine_depletion_factor("coal")
          - (two.mine_depletion_factor_for(older) * 40.0 + two.mine_depletion_factor_for(newer) * 20.0) / 60.0) < 1e-12,
      two.mine_depletion_factor("coal"))
check("rated capacity is summed over the workings of a material", two.mine_capacity == {"coal": 60.0}, two.mine_capacity)
check("a material with no workings has no history: depletion is one", two.mine_depletion_factor("tin") == 1.0, None)

# --- the cost scale is depletion inverted, bounded on both ends.
fresh = _Founder()
fresh_working = fresh.add_working()
check("a fresh working costs book: scale one", fresh.mining_cost_scale_for(fresh_working) == 1.0,
      fresh.mining_cost_scale_for(fresh_working))
half = _Founder()
half_working = half.add_working(intensity=half.DEPLETION_HALF_LIFE_YRS / 2.0)
check("a working that has lost a share of its yield costs the inverse share more",
      abs(half.mining_cost_scale_for(half_working) - 1.0 / half.mine_depletion_factor_for(half_working)) < 1e-12,
      half.mining_cost_scale_for(half_working))
worn = _Founder()
worn_working = worn.add_working(intensity=1e9)
check("fully depleted, a tonne costs more than book but never more than the ceiling multiple",
      1.0 < worn.mining_cost_scale_for(worn_working) <= worn.MINING_COST_SCALE_CEILING,
      worn.mining_cost_scale_for(worn_working))
check("the material's scale agrees with its only working's", worn.mining_cost_scale("coal") == worn.mining_cost_scale_for(worn_working), None)
check("the cost scale bounds are a real floor below one and a ceiling above one",
      0.0 < worn.MINING_COST_SCALE_FLOOR < 1.0 < worn.MINING_COST_SCALE_CEILING, None)

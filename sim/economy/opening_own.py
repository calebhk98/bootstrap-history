"""What the opening's households grow on their own plots, so the demand producers are sized to is what they buy.

A year's households put the hours nobody hired into their plots (`Economy._grow_own`, `households_own.own_production`)
and cut each floor bid by the share of the floor they grew (`year_goods.less_what_it_grew`). The opening runs the same
two functions: the hours a cohort has left are its working hours less the share the producers hire and the household
work it does itself, and the bids it then makes are the year's. The share the producers hire follows from the runs
sized to that demand, so the opening iterates it (`_settle_income` in opening.py) until it stops moving (Complaint 545)."""
import math
from typing import Dict, Mapping, Tuple

from . import household_grinding, households_own, households_work, titles_plots, year_goods
from .household_work_year import has_hearth
from .types import GoodId


def hired_share(runs: Mapping[str, float], recipes: Mapping[str, object], hands_hours: float) -> float:
    """The share of the working hours a year that producers of `runs` hire: one when they need all of them or more."""
    needed = math.fsum(count * math.fsum(recipes[recipe_id].labour_hours.values()) for recipe_id, count in runs.items())
    return 0.0 if hands_hours <= 0.0 else min(1.0, needed / hands_hours)


def idle_hours(hours: float, share_hired: float, own_work_hours: float) -> float:
    """Hours a cohort has for its plot: its working hours less those producers hire and the household work it does itself."""
    return max(0.0, hours * (1.0 - share_hired) - own_work_hours)


class OwnPlots:
    """The own-plot rule of a year applied to an opening record's cohorts, at the share of hours producers hire."""

    def __init__(self, setup, record) -> None:
        self.setup = setup
        self.options = households_own.own_production_options(setup.recipes, setup.land_per_run, setup.basket)
        self.held = titles_plots.hectares_held(setup, record)
        self.share_hired = 0.0
        self.grown: Dict[str, Dict[GoodId, float]] = {}     # cohort -> goods grown at the last ask
        self.uncut: Dict[str, Tuple[float, object]] = {}   # cohort -> (income, orders before the cut): the asks of one income share them
        self.in_kind = 0.0      # budget the cuts of the asks since it was last zeroed freed: spent on its own plot, not saved

    def note_runs(self, runs: Mapping[str, float], hands_hours: float) -> float:
        """Take the hired share the runs imply; returns how far it moved."""
        updated = hired_share(runs, self.setup.recipes, hands_hours)
        moved = abs(updated - self.share_hired)
        self.share_hired = updated
        return moved

    def own_work_hours(self, record, cohort, priced) -> float:
        """Hours of household work the cohort does itself (household_work_year.cohort_plan): the work its people need,
        with the grain it grinds by hand, less the hours it hires."""
        setup = self.setup
        if not setup.household_work:
            return 0.0
        food = next((need for need in priced if need.spec.need_id == setup.hunger_need), None)
        ground = household_grinding.ground_share(food.goods, setup.milled_as, cohort.milled_grains) if food is not None and setup.milled_as else 1.0
        needed = households_work.hours_needed(cohort.people, setup.household_work, has_hearth(record, cohort), ground)
        return households_work.own_hours(needed, cohort.hired_work_per_person * cohort.people)

    def orders_at(self, cohort, income, make):
        """The cohort's orders at `income` before the cut, made by `make()` the first time the income is asked."""
        held = self.uncut.get(cohort.agent_id)
        if held is None or held[0] != income:
            held = self.uncut[cohort.agent_id] = (income, make())
        return held[1]

    def less_grown(self, record, cohort, orders, basket, priced):
        """The cohort's orders with each floor cut by the share of it the cohort's plot grows."""
        setup = self.setup
        tile = setup.tiles.get(cohort.tile)
        idle = idle_hours(cohort.working_people * setup.working_hours_per_year, self.share_hired,
                          self.own_work_hours(record, cohort, priced))
        _moves, grown, units = households_own.own_production(
            cohort, idle, self.options, setup.recipes, tile.fertility if tile else 0.0, setup.basket_for(cohort.tile),
            setup.land_per_run, self.held.get(cohort.agent_id, 0.0))
        self.grown[cohort.agent_id] = grown
        cut = year_goods.less_what_it_grew(orders, cohort, basket, units)
        self.in_kind += math.fsum(bid.budget for bid in orders.bids) - math.fsum(bid.budget for bid in cut.bids)
        return cut

    def grown_totals(self) -> Dict[GoodId, float]:
        """Goods the cohorts grow in all, at the last ask."""
        total: Dict[GoodId, float] = {}
        for grown in self.grown.values():
            for good, quantity in grown.items():
                total[good] = total.get(good, 0.0) + quantity
        return dict(sorted(total.items()))

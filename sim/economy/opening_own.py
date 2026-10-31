"""What the opening's households grow on their own plots, so the demand producers are sized to is what they buy.

A year's households put the hours nobody hired into their plots (`Economy._grow_own`, `households_own.own_production`)
and cut each floor bid by the share of the floor they grew (`year_goods.less_what_it_grew`). The opening runs the same
two functions: the hours a cohort has left are its working hours less the share the producers hire and the household
work it does itself, and the bids it then makes are the year's. The share the producers hire follows from the runs
sized to that demand, so the opening iterates it (`_settle_income` in opening.py) until it stops moving (Complaint 545)."""
import math
from typing import Dict, Mapping, Tuple

from . import household_grinding, household_hours_year, households_orders, households_own, households_work, labour_ask_floor, labour_supply, opening_resting, titles_plots, year_goods
from .household_work_year import has_hearth
from .types import GoodId

PURSE_PASSES = 3            # numerical bound on the purse that matches the budget its plot frees
PURSE_TOLERANCE = 1e-6      # relative to income


def hired_share(runs: Mapping[str, float], recipes: Mapping[str, object], hands_hours: float) -> float:
    """The share of the working hours a year that producers of `runs` hire: one when they need all of them or more."""
    needed = math.fsum(count * math.fsum(recipes[recipe_id].labour_hours.values()) for recipe_id, count in runs.items())
    return 0.0 if hands_hours <= 0.0 else min(1.0, needed / hands_hours)


def idle_hours(hours: float, share_hired: float, own_work_hours: float) -> float:
    """Hours a cohort has for its plot: its working hours less those producers hire and the household work it does itself."""
    return max(0.0, hours * (1.0 - share_hired) - own_work_hours)


def sold_hours(whole: float, plan_hours: float, plot_hours: float, work_hours: float) -> float:
    """Hours of a cohort's `whole` year its households sell at the opening wage under the year's own rule
    (labour_supply.hours_kept_at_home): what the plan, the plot at that wage and the household work leave."""
    return whole - labour_supply.hours_kept_at_home(whole, plan_hours, plot_hours, work_hours)


def sold_hours_per_worker(sold_total: float, working_people: float, default: float) -> float:
    """Hours a working person sells a year at rest, the `default` (a whole year) where nobody works."""
    return sold_total / working_people if working_people > 0.0 else default


class OwnPlots:
    """The own-plot rule of a year applied to an opening record's cohorts, at the share of hours producers hire."""

    def __init__(self, setup, record) -> None:
        self.setup = setup
        self.options = households_own.own_production_options(setup.recipes, setup.land_per_run, setup.basket)
        self.held = titles_plots.hectares_held(setup, record)
        self.share_hired = 0.0
        self.grown: Dict[str, Dict[GoodId, float]] = {}     # cohort -> goods grown at the last ask
        self.uncut: Dict[str, Tuple[float, object]] = {}   # cohort -> (income, orders before the cut): the asks of one income share them
        self.extra: Dict[str, float] = {}   # cohort -> spending beyond its income that its purse allows (what its plot frees)
        self.in_kind = 0.0      # budget the cuts freed that the rule cannot spend on the market, since it was last zeroed
        self.sold: Dict[str, float] = {}    # cohort -> hours it sells at the opening wage, at the last ask
        self.kept_at_home: Dict[str, Tuple[float, float]] = {}   # cohort -> (plan hours, plot hours at the opening wage): neither moves with income
        self.hectares_per_hour = labour_ask_floor.hectares_per_hour_by_recipe(setup.recipes, setup.land_per_run)

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

    def resting_orders(self, record, cohort, income, basket, priced, make):
        """The cohort's orders as a year-one household with this income would make them, after its plot: `make(cash)` gives
        its orders (before the cut) holding `cash`. The floors its plot grows are cut after the budget is set, so the
        cohort holds the purse that makes the budget that much larger than its income (opening_resting): it spends on
        the market what it earns and the plot's share of the budget is not saved. The rule lets it spend beyond its income
        only up to WEALTH_DRAWDOWN_LIMIT of the income; what that does not cover is spent in kind (`in_kind`)."""
        held = self.uncut.get(cohort.agent_id)
        purse = held[2] if held is not None and held[0] == income else 0.0
        for _pass in range(PURSE_PASSES):
            if held is None or held[0] != income or held[2] != purse:
                held = self.uncut[cohort.agent_id] = (income, make(income + purse), purse)
            cut, freed = self._cut(record, cohort, held[1], basket, priced)
            extra = min(freed, households_orders.WEALTH_DRAWDOWN_LIMIT * income)
            wanted = opening_resting.resting_household_purse(income, 0.0, 0.0, extra)
            self.extra[cohort.agent_id] = extra
            if abs(wanted - purse) <= PURSE_TOLERANCE * max(income, 1e-9):
                break
            purse = wanted
        self.in_kind += freed - extra
        return cut

    def _cut(self, record, cohort, orders, basket, priced):
        """(the orders with each floor cut by the share of it the cohort's plot grows, the budget that frees)."""
        setup = self.setup
        tile = setup.tiles.get(cohort.tile)
        own_work = self.own_work_hours(record, cohort, priced)
        idle = idle_hours(cohort.working_people * setup.working_hours_per_year, self.share_hired, own_work)
        _moves, grown, units = households_own.own_production(
            cohort, idle, self.options, setup.recipes, tile.fertility if tile else 0.0, setup.basket_for(cohort.tile),
            setup.land_per_run, self.held.get(cohort.agent_id, 0.0))
        self.grown[cohort.agent_id] = grown
        self.sold[cohort.agent_id] = self._sold_hours(cohort, priced, own_work)
        cut = year_goods.less_what_it_grew(orders, cohort, basket, units)
        return cut, math.fsum(bid.budget for bid in orders.bids) - math.fsum(bid.budget for bid in cut.bids)

    def _sold_hours(self, cohort, priced, own_work: float) -> float:
        """The hours the cohort sells at the opening wage when the year runs (labour_supply.HourSupply): the hours its
        own-plot plan, its plot at that wage (household_hours_year) and its household work keep back are not sold."""
        setup = self.setup
        if cohort.agent_id not in self.kept_at_home:
            tile = setup.tiles.get(cohort.tile)
            held = self.held.get(cohort.agent_id, 0.0)
            plan = households_own.hours_for_own_plan(cohort, self.options, tile.fertility if tile else 0.0, setup.recipes,
                                                     setup.land_per_run, held)
            schedule = household_hours_year.cohort_plot_schedule(
                setup, cohort, cohort.working_people * setup.working_hours_per_year, priced, self.options, held,
                self.hectares_per_hour)
            wage = setup.opening_wages.get(setup.unskilled_trade, 0.0)
            self.kept_at_home[cohort.agent_id] = (plan, schedule(wage) if schedule is not None else 0.0)
        plan, plot = self.kept_at_home[cohort.agent_id]
        return sold_hours(cohort.working_people * setup.working_hours_per_year, plan, plot, own_work)

    def sold_total(self) -> float:
        """Hours the cohorts sell in all at the opening wage, at the last ask."""
        return math.fsum(self.sold[agent_id] for agent_id in sorted(self.sold))

    def grown_totals(self) -> Dict[GoodId, float]:
        """Goods the cohorts grow in all, at the last ask."""
        total: Dict[GoodId, float] = {}
        for grown in self.grown.values():
            for good, quantity in grown.items():
                total[good] = total.get(good, 0.0) + quantity
        return dict(sorted(total.items()))

"""The hours households sell, as a schedule against the wage (Complaints 473, 608, 675).

A household's year of hours goes first to its own-plot plan and the household work it does itself (both fixed for the
year), then to its plot as far as an hour there beats the wage (`households_hours_offered.plot_hours_kept`); every
other hour is offered to the market, with no leisure split. Eurace@Unibi households have no hours decision at all
(Labour/Household_Employee_Functions.c); the plot choice is this model's own. The labour core clears each market
against the hours its offers hold (`YearInputs.hours_sold_at`); after it, the hours each offer sold and the hours kept
for each use are read at the wage the market cleared at.

The offers are a table (`labour_offers_table.LabourOffers`) and the schedule, the matrix the clearing kernel reads and the
settlement are kernels over it (`labour_offers_kernels`). `HourSupply` is the Python wrapper for callers not yet on the table.
Where a plot rule is a bare function (no parameters to put in a column), the supply is summed offer by offer
(`labour_supply_plain`); that is also the path a rule replaced by a mod takes.
"""
import dataclasses
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy

from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY

from . import household_hours_year, labour_offers_kernels, labour_supply_plain
from .labour_offers_table import PlotParameters, build_labour_offers
from .labour_supply_markets import MarketHours
from .types import AgentId, LabourOffer


def hours_kept_at_home(whole: float, plan_hours: float, plot_hours: float, work_hours: float) -> float:
    """Hours of a cohort's `whole` year that go home: the plot keeps what its plan or its wage-driven choice asks (the
    greater), the household work comes beside it, and no more than the year goes."""
    return min(max(plan_hours, plot_hours) + work_hours, whole)


@dataclasses.dataclass
class HourSupply:
    offers: Sequence[LabourOffer]                       # every offer, with the cohort's whole year of hours
    plan_hours: Mapping[AgentId, float]                 # own-plot plan hours a cohort keeps whatever the wage
    work_hours: Mapping[AgentId, float]                 # household work it does itself
    plot_hours_at: Mapping[AgentId, Callable[[float], float]]   # hours its plot keeps at a wage (households_hours_offered.plot_hours_kept); one with `.parameters` goes into the table, any other makes the supply plain
    faced_wage: Mapping[Tuple[str, str], float] = dataclasses.field(default_factory=dict)   # (trade, area) -> wage where no market cleared
    # filled by `settle`
    sold: List[LabourOffer] = dataclasses.field(default_factory=list)
    kept: Dict[AgentId, float] = dataclasses.field(default_factory=dict)
    plot_parameters: Mapping[AgentId, PlotParameters] = dataclasses.field(default_factory=dict)   # the plot rule as numbers (household_hours_year.plot_parameters_by_cohort): no closure needed

    def __post_init__(self) -> None:
        self._parameters: Dict[AgentId, PlotParameters] = dict(self.plot_parameters)
        self._bare_plots: Dict[AgentId, Callable[[float], float]] = {}
        for cohort, plot in self.plot_hours_at.items():
            parameters = getattr(plot, "parameters", None)
            if parameters is None:
                self._bare_plots[cohort] = plot
            else:
                self._parameters.setdefault(cohort, PlotParameters(*parameters))
        self._whole: Optional[Dict[AgentId, float]] = None
        self._parts = None                  # (table, ids, markets), built on first use
        self._market_hours: Optional[MarketHours] = None

    @property
    def _hours(self) -> Dict[AgentId, float]:
        """Each cohort's hours over its offers (the year the home share is taken from)."""
        if self._whole is None:
            self._whole = {}
            for offer in self.offers:
                self._whole[offer.worker] = self._whole.get(offer.worker, 0.0) + offer.hours
        return self._whole

    @property
    def table(self):
        """The `LabourOffers` table of these offers (labour_offers_table.py); sold and kept hours are filled by `settle`."""
        return self._build()[0]

    def _build(self):
        if self._parts is None:
            self._parts = build_labour_offers(self.offers, self.plan_hours, self.work_hours, self._parameters)
        return self._parts

    def _plot(self, worker: AgentId) -> Optional[Callable[[float], float]]:
        """The cohort's plot schedule as a function of the wage, for the offer-by-offer rule."""
        if worker in self._bare_plots:
            return self._bare_plots[worker]
        parameters = self._parameters.get(worker)
        return household_hours_year.plot_schedule(*parameters) if parameters is not None else None

    def split(self, offer: LabourOffer, wage: float) -> Tuple[float, float]:
        """(hours sold, hours kept for plot and household work) of one offer at this wage: every hour the plot and the
        household work do not take is sold. The reference rule: the kernels are tested against it."""
        whole = self._hours.get(offer.worker, 0.0)
        if whole <= 0.0 or offer.hours <= 0.0:
            return 0.0, 0.0
        plot = self._plot(offer.worker)
        at_home = hours_kept_at_home(whole, self.plan_hours.get(offer.worker, 0.0), plot(wage) if plot else 0.0,
                                     self.work_hours.get(offer.worker, 0.0)) * offer.hours / whole
        return offer.hours - at_home, at_home

    def sold_hours_schedule(self, offer: LabourOffer) -> Callable[[float], float]:
        """The hours of one offer sold at a wage, as `split(offer, wage)[0]` gives them, with what does not depend on
        the wage worked out once: for a schedule asked at many wages."""
        whole = self._hours.get(offer.worker, 0.0)
        if whole <= 0.0 or offer.hours <= 0.0:
            return lambda wage: 0.0
        plot = self._plot(offer.worker)
        plan = self.plan_hours.get(offer.worker, 0.0)
        work = self.work_hours.get(offer.worker, 0.0)
        share = offer.hours / whole
        hours = offer.hours

        def sold(wage: float) -> float:
            return hours - hours_kept_at_home(whole, plan, plot(wage) if plot else 0.0, work) * share
        return sold

    def hours_at(self, trade: str, area: str) -> Callable[[float], float]:
        """The hours sold at a wage in one market: the sum over its offers."""
        if self._bare_plots:
            return labour_supply_plain.hours_over(self, [offer for offer in self.offers if offer.trade == trade and offer.area == area])
        found = self.schedules().get((trade, area))
        return found if found is not None else (lambda wage: 0.0)

    def schedules(self):
        """`hours_at` for every market that has an offer; a market without one sells nothing. The mapping a year's
        `hours_sold_at` is (`labour_supply_markets.MarketHours` unless a bare plot rule makes it plain)."""
        if self._bare_plots:
            return labour_supply_plain.schedules(self)
        if self._market_hours is None:
            table, ids, markets = self._build()
            matrix, first, last = labour_offers_kernels.offer_matrix(table, len(markets))
            self._market_hours = MarketHours(matrix, 1.0 / (1.0 - LABOUR_OUTPUT_ELASTICITY), ids.market_names(
                markets.trade_of_market, markets.area_of_market), first, last)
        return self._market_hours

    def settle(self, wage_by_market: Mapping[Tuple[str, str], float]) -> List[LabourOffer]:
        """The offers as sold at the wages the markets cleared at (the faced wage where one did not), and the hours each
        cohort kept in all."""
        if self._bare_plots:
            return labour_supply_plain.settle(self, wage_by_market)
        table, ids, markets = self._build()
        names = self.schedules().markets
        wage = numpy.zeros(len(names))
        known = numpy.zeros(len(names), dtype=numpy.bool_)
        for position, market in enumerate(names):
            found = wage_by_market.get(market, self.faced_wage.get(market))
            if found is not None:
                wage[position], known[position] = found, True
        kept_by_cohort = labour_offers_kernels.settle_offers(table, wage, known, self._market_hours.exponent, len(ids.cohorts))
        self.sold = [LabourOffer(offer.worker, offer.trade, offer.area, sold, offer.reservation_wage)
                     for offer, sold in zip(self.offers, table.sold_hours.tolist())]
        cohorts, first_row = numpy.unique(table.cohort, return_index=True)      # kept lists cohorts in the order their first offer came
        cohort_numbers, kept_hours = cohorts.tolist(), kept_by_cohort.tolist()
        self.kept = {ids.cohorts.name(cohort_numbers[each]): kept_hours[cohort_numbers[each]] for each in numpy.argsort(first_row).tolist()}
        return self.sold

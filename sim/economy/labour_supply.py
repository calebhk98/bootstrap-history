"""The hours households sell, as a schedule against the wage (Complaints 473, 608, 675).

A household's year of hours goes first to its own-plot plan and the household work it does itself (both fixed for the
year), then to its plot as far as an hour there beats the wage (`households_hours_offered.plot_hours_kept`); every
other hour is offered to the market, with no leisure split. Eurace@Unibi households have no hours decision at all
(Labour/Household_Employee_Functions.c); the plot choice is this model's own. The labour core clears each market
against the hours its offers hold (`YearInputs.hours_sold_at`); after it, the hours each offer sold and the hours kept
for each use are read at the wage the market cleared at. Plain functions of built inputs.
"""
import dataclasses
from typing import Callable, Dict, List, Mapping, Sequence, Tuple

from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY

from . import labour_supply_kernel
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
    plot_hours_at: Mapping[AgentId, Callable[[float], float]]   # hours its plot keeps at a wage (households_hours_offered.plot_hours_kept)
    faced_wage: Mapping[Tuple[str, str], float] = dataclasses.field(default_factory=dict)   # (trade, area) -> wage where no market cleared
    # filled by `settle`
    sold: List[LabourOffer] = dataclasses.field(default_factory=list)
    kept: Dict[AgentId, float] = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        self._hours: Dict[AgentId, float] = {}
        for offer in self.offers:
            self._hours[offer.worker] = self._hours.get(offer.worker, 0.0) + offer.hours

    def split(self, offer: LabourOffer, wage: float) -> Tuple[float, float]:
        """(hours sold, hours kept for plot and household work) of one offer at this wage: every hour the plot and the
        household work do not take is sold."""
        whole = self._hours.get(offer.worker, 0.0)
        if whole <= 0.0 or offer.hours <= 0.0:
            return 0.0, 0.0
        plot = self.plot_hours_at.get(offer.worker)
        at_home = hours_kept_at_home(whole, self.plan_hours.get(offer.worker, 0.0), plot(wage) if plot else 0.0,
                                     self.work_hours.get(offer.worker, 0.0)) * offer.hours / whole
        return offer.hours - at_home, at_home

    def sold_hours_schedule(self, offer: LabourOffer) -> Callable[[float], float]:
        """The hours of one offer sold at a wage, as `split(offer, wage)[0]` gives them, with what does not depend on
        the wage worked out once: for a schedule asked at many wages."""
        whole = self._hours.get(offer.worker, 0.0)
        if whole <= 0.0 or offer.hours <= 0.0:
            return lambda wage: 0.0
        plot = self.plot_hours_at.get(offer.worker)
        plan = self.plan_hours.get(offer.worker, 0.0)
        work = self.work_hours.get(offer.worker, 0.0)
        share = offer.hours / whole
        hours = offer.hours

        def sold(wage: float) -> float:
            return hours - hours_kept_at_home(whole, plan, plot(wage) if plot else 0.0, work) * share
        return sold

    def hours_at(self, trade: str, area: str) -> Callable[[float], float]:
        """The hours sold at a wage in one market: the sum over its offers."""
        return self._hours_over([offer for offer in self.offers if offer.trade == trade and offer.area == area])

    def _hours_over(self, in_market: Sequence[LabourOffer]) -> Callable[[float], float]:
        live = [offer for offer in in_market if offer.hours > 0.0]
        packed = self._packed(live) if live else labour_supply_kernel.pack_offers([])
        exponent = 1.0 / (1.0 - LABOUR_OUTPUT_ELASTICITY)
        if packed is not None:
            def packed_hours(wage: float) -> float:
                return labour_supply_kernel.sold_hours(wage, packed, exponent)
            packed_hours.packed = (packed, exponent)      # the labour core reads every market's offers from here into one kernel
            return packed_hours
        schedules = [self.sold_hours_schedule(offer) for offer in live]

        def hours(wage: float) -> float:
            return sum([schedule(wage) for schedule in schedules])
        return hours

    def _packed(self, live: Sequence[LabourOffer]):
        """The market's offers as arrays for the kernel, or None where a plot schedule is not the parametric one."""
        rows = []
        for offer in live:
            whole = self._hours.get(offer.worker, 0.0)
            plot = self.plot_hours_at.get(offer.worker)
            parameters = getattr(plot, "parameters", None) if plot else None
            if whole <= 0.0 or (plot and parameters is None):
                return None
            rows.append((offer.hours, whole, self.plan_hours.get(offer.worker, 0.0), self.work_hours.get(offer.worker, 0.0), parameters))
        return labour_supply_kernel.pack_offers(rows)

    def schedules(self) -> Dict[Tuple[str, str], Callable[[float], float]]:
        """`hours_at` for every market that has an offer; a market without one sells nothing."""
        by_market: Dict[Tuple[str, str], List[LabourOffer]] = {}
        for offer in self.offers:
            by_market.setdefault((offer.trade, offer.area), []).append(offer)
        return {market: self._hours_over(by_market[market]) for market in sorted(by_market)}

    def settle(self, wage_by_market: Mapping[Tuple[str, str], float]) -> List[LabourOffer]:
        """The offers as sold at the wages the markets cleared at (the faced wage where one did not), and the hours
        each cohort kept in all."""
        self.sold, self.kept = [], {}
        for offer in self.offers:
            market = (offer.trade, offer.area)
            wage = wage_by_market.get(market, self.faced_wage.get(market, offer.reservation_wage))
            sold, _at_home = self.split(offer, wage)
            self.sold.append(LabourOffer(offer.worker, offer.trade, offer.area, sold, offer.reservation_wage))
            self.kept[offer.worker] = self.kept.get(offer.worker, 0.0) + (offer.hours - sold)
        return self.sold
